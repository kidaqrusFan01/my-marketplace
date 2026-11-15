from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from cart.cart import Cart
from products.views import seller_required
from loyalty.models import LoyaltyAccount
from loyalty.services import award_purchase_points
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .notifications import notify_sellers_of_order, notify_agents_of_shared_order


@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('products:home')

    loyalty_account = LoyaltyAccount.get_or_create_for(request.user)
    subtotal = cart.get_total_price()

    if request.method == 'POST':
        form = OrderCreateForm(
            request.POST,
            available_points=loyalty_account.balance,
            order_subtotal=subtotal,
        )
        if form.is_valid():
            points_to_redeem = form.cleaned_data.pop('points_to_redeem', 0) or 0

            with transaction.atomic():
                order = form.save(commit=False)
                order.customer = request.user
                order.save()

                for item in cart:
                    product = item['product']
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        price=item['price'],
                        quantity=item['quantity'],
                    )
                    # Decrement stock
                    product.stock = max(product.stock - item['quantity'], 0)
                    product.save()

                if points_to_redeem > 0:
                    redemption_txn = loyalty_account.redeem(
                        points_to_redeem, reason='redeemed_discount', related_order=order,
                        note=f"Applied to Order #{order.id}",
                    )
                    if redemption_txn is not None:
                        order.loyalty_points_redeemed = points_to_redeem
                        order.loyalty_discount_amount = points_to_redeem  # 1 point = ₦1
                        order.save(update_fields=['loyalty_points_redeemed', 'loyalty_discount_amount'])

            # Points are earned on what was actually bought, so this runs
            # after the order (and its items) are committed.
            award_purchase_points(order)

            # Let each seller know their product was ordered.
            notify_sellers_of_order(order, request)

            # ...and tell any Agent whose shared link brought this customer.
            notify_agents_of_shared_order(order, request)

            cart.clear()
            messages.success(request, "Your order was placed successfully!")
            return redirect('orders:order_complete', order_id=order.id)
    else:
        initial = {
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'address': request.user.address,
            'phone_number': request.user.phone_number,
        }
        form = OrderCreateForm(initial=initial, available_points=loyalty_account.balance, order_subtotal=subtotal)

    return render(request, 'orders/create.html', {
        'cart': cart, 'form': form, 'loyalty_balance': loyalty_account.balance,
    })


@login_required
def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'orders/complete.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'orders/history.html', {'orders': orders})


@seller_required
def seller_orders(request):
    """
    "Orders Received": every order that includes this seller's products,
    newest first, showing ONLY this seller's line items (never another
    seller's items from the same order) plus the delivery details they
    need to fulfil it.
    """
    items = (
        OrderItem.objects.filter(product__seller=request.user)
        .select_related('order', 'product')
        .order_by('-order__created_at', 'id')
    )
    grouped = {}
    for item in items:
        entry = grouped.setdefault(item.order_id, {'order': item.order, 'items': [], 'total': 0})
        entry['items'].append(item)
        entry['total'] += item.get_cost()
    return render(request, 'orders/seller_orders.html', {'received': list(grouped.values())})
