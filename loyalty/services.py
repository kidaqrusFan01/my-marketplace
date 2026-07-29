"""
Business logic for awarding loyalty points on a completed purchase.

Kept separate from views/models so both orders.views (checkout) and any
future code path (e.g. an admin action to re-run rewards) can call the
same, single source of truth for "how many points does this order earn".
"""
from django.utils import timezone

from . import constants
from .models import LoyaltyAccount


def product_is_current_deal(product):
    """True if `product` is the live Deal of the Day right now."""
    if product is None:
        return False
    from products.models import DealOfTheDay
    now = timezone.now()
    return DealOfTheDay.objects.filter(
        product=product, is_active=True, starts_at__lte=now, ends_at__gte=now
    ).exists()


def award_purchase_points(order):
    """
    Call once, right after an order is successfully placed. Awards:
      1. Ordinary purchase points (POINTS_PER_100_NAIRA_SPENT per ₦100 of
         the order's subtotal — loyalty discounts already applied don't
         reduce this, points are earned on what was actually bought).
      2. A flat bonus for each line item that was bought at the Deal of
         the Day price.
      3. If this is the buyer's very first order AND they signed up via
         someone's referral link, a one-time bonus to that referrer.
    """
    account = LoyaltyAccount.get_or_create_for(order.customer)
    items = list(order.items.select_related('product'))

    subtotal = order.get_subtotal()
    base_points = int(subtotal // 100) * constants.POINTS_PER_100_NAIRA_SPENT
    if base_points > 0:
        account.award(base_points, reason='purchase', related_order=order, note=f"Order #{order.id}")

    deal_items = [item for item in items if product_is_current_deal(item.product)]
    if deal_items:
        bonus = constants.DEAL_OF_DAY_PURCHASE_BONUS * len(deal_items)
        account.award(
            bonus, reason='deal_of_day_purchase_bonus', related_order=order,
            note=f"Deal of the Day bonus ({len(deal_items)} item(s))",
        )

    _maybe_award_referrer(order, items)


def _maybe_award_referrer(order, items):
    customer = order.customer
    referrer = customer.referred_by
    if not referrer:
        return

    # Only ever reward the customer's FIRST completed order — otherwise
    # the referrer would get paid again on every future order this same
    # customer places, which isn't the point of a referral bonus.
    from orders.models import Order
    if Order.objects.filter(customer=customer).count() != 1:
        return

    multiplier = constants.DEAL_OF_DAY_MULTIPLIER if any(
        product_is_current_deal(item.product) for item in items
    ) else 1

    referrer_account = LoyaltyAccount.get_or_create_for(referrer)
    referrer_account.award(
        constants.REFERRAL_PURCHASE_POINTS * multiplier,
        reason='referral_purchase', related_order=order,
        note=f"{customer.username}'s first purchase",
    )
    referrer_account.award(
        constants.NEW_BUYER_BONUS_POINTS * multiplier,
        reason='new_buyer_bonus', related_order=order,
        note=f"{customer.username} was a new buyer",
    )
