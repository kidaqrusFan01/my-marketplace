from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem


@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('products:home')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
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
        form = OrderCreateForm(initial=initial)

    return render(request, 'orders/create.html', {'cart': cart, 'form': form})


@login_required
def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'orders/complete.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'orders/history.html', {'orders': orders})
