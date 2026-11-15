"""
Tells sellers when someone orders their product.

Called once per order, right after checkout succeeds. Each seller involved
gets ONE alert for the order (even if it contains several of their items, or
items from other sellers), listing only their own line items:

  * an in-site notification (bell in the nav + /notifications/), and
  * an email to the seller's account address, if they have one.

The email deliberately leaves out the buyer's address and phone number —
those are only shown on the seller's logged-in "Orders Received" page.
"""
import logging
from collections import OrderedDict

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from accounts.models import CustomUser
from loyalty.models import LoyaltyTransaction
from notifications.models import Notification
from products.templatetags.currency_filters import naira

logger = logging.getLogger(__name__)


def _group_items_by_seller(order):
    groups = OrderedDict()
    for item in order.items.select_related('product__seller'):
        product = item.product
        if product is None:          # product deleted after purchase — nobody to tell
            continue
        groups.setdefault(product.seller, []).append(item)
    return groups


def notify_sellers_of_order(order, request=None):
    """Never raises — a notification problem must not break someone's checkout."""
    try:
        groups = _group_items_by_seller(order)
    except Exception:
        logger.exception("Could not work out sellers for order #%s", order.pk)
        return

    orders_path = reverse('orders:seller_orders')
    orders_url = request.build_absolute_uri(orders_path) if request else orders_path

    for seller, items in groups.items():
        if seller.pk == order.customer_id:
            continue   # a seller buying their own product doesn't need an alert about it

        item_lines = [f"{i.quantity} × {i.product_name} — {naira(i.get_cost())}" for i in items]
        total = naira(sum(i.get_cost() for i in items))
        count = sum(i.quantity for i in items)
        headline = (
            f"New order #{order.pk}: {items[0].product_name}" if len(items) == 1
            else f"New order #{order.pk}: {len(items)} of your products"
        )

        try:
            Notification.objects.create(
                recipient=seller, kind='order_received', title=headline,
                message="\n".join(item_lines) + f"\nYour items total: {total}",
                url=orders_path,
            )
        except Exception:
            logger.exception("Could not create in-site notification for seller #%s (order #%s)", seller.pk, order.pk)

        if not seller.email:
            continue
        body = "\n".join([
            f"Hi {seller.store_name or seller.username},",
            "",
            f"Good news — a customer just placed order #{order.pk} that includes "
            f"{'your product' if count == 1 else 'your products'}:",
            "",
            *[f"  • {line}" for line in item_lines],
            "",
            f"Your items total: {total}",
            "",
            f"See the delivery details and get it ready: {orders_url}",
            "",
            "— Corazon Marketplace",
        ])
        try:
            send_mail(
                subject=f"🛒 You have a new order (#{order.pk}) — {total}",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[seller.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Could not email seller #%s about order #%s", seller.pk, order.pk)


# ---------------------------------------------------------------------------
# Agents: "a product you shared was just ordered"
# ---------------------------------------------------------------------------

def _agents_who_brought_this_buyer(order, request):
    """
    Agents whose link brought this customer: the one whose ?ref= code is in
    the buyer's browser session (they followed that agent's shared link), and
    the agent they originally signed up through. Duplicates are collapsed.
    """
    agents = {}
    ref_code = request.session.get('referral_code') if request is not None else None
    if ref_code:
        for user in CustomUser.objects.filter(referral_code=ref_code):
            agents[user.pk] = user
    referrer = order.customer.referred_by
    if referrer is not None:
        agents[referrer.pk] = referrer
    return [a for a in agents.values() if a.is_agent and a.pk != order.customer_id]


def notify_agents_of_shared_order(order, request=None):
    """
    Tells an Agent when a customer orders a product that THEY shared, and the
    customer came through that agent's link. An agent is only told about the
    items they actually shared — not the rest of the basket — and never about
    their own purchases or products they sell themselves (sellers already get
    the order alert). The alert holds no buyer details at all.

    Never raises: a notification problem must not break anyone's checkout.
    """
    try:
        items = [i for i in order.items.select_related('product') if i.product is not None]
        candidates = _agents_who_brought_this_buyer(order, request)
    except Exception:
        logger.exception("Could not work out agents for order #%s", order.pk)
        return

    agent_path = reverse('agents:page')
    agent_url = request.build_absolute_uri(agent_path) if request else agent_path

    for agent in candidates:
        try:
            shared_ids = set(
                LoyaltyTransaction.objects.filter(
                    account__user=agent, reason='share',
                    related_product_id__in=[i.product_id for i in items],
                ).values_list('related_product_id', flat=True)
            )
        except Exception:
            logger.exception("Could not look up shares for agent #%s (order #%s)", agent.pk, order.pk)
            continue

        matching = [i for i in items if i.product_id in shared_ids and i.product.seller_id != agent.pk]
        if not matching:
            continue

        item_lines = [f"{i.quantity} × {i.product_name} — {naira(i.get_cost())}" for i in matching]
        total = naira(sum(i.get_cost() for i in matching))
        title = (
            f"A customer ordered {matching[0].product_name}, which you shared" if len(matching) == 1
            else f"A customer ordered {len(matching)} products you shared"
        )

        try:
            Notification.objects.create(
                recipient=agent, kind='shared_product_ordered', title=title,
                message="\n".join(item_lines) + f"\nOrder value for what you shared: {total}",
                url=agent_path,
            )
        except Exception:
            logger.exception("Could not create in-site notification for agent #%s (order #%s)", agent.pk, order.pk)

        if not agent.email:
            continue
        name = getattr(getattr(agent, 'agent_profile', None), 'display_name', None) or agent.username
        body = "\n".join([
            f"Hi {name},",
            "",
            "Your sharing paid off — a customer who came through your link just ordered "
            + ("a product" if len(matching) == 1 else "products") + " you shared:",
            "",
            *[f"  • {line}" for line in item_lines],
            "",
            f"Order value for what you shared: {total}",
            "",
            f"See your sharing activity: {agent_url}",
            "",
            "Keep sharing! — Corazon Marketplace",
        ])
        try:
            send_mail(
                subject=f"🎯 A product you shared was just ordered — {total}",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[agent.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Could not email agent #%s about a shared-product order", agent.pk)
