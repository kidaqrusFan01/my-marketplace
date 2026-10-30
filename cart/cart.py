from decimal import Decimal
from products.models import Product

CART_SESSION_ID = 'cart'


class Cart:
    """
    Session-based shopping cart. Works for both anonymous and
    logged-in users without needing a database table.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart
        self._drop_unavailable_items()

    def _drop_unavailable_items(self):
        """If a product was added to the cart and later became hidden (seller
        switched it off, or an admin revoked the seller's approval), quietly
        remove it so checkout never tries to sell something shoppers can no
        longer see."""
        if not self.cart:
            return
        still_visible = set(
            str(pk) for pk in Product.objects.visible()
            .filter(id__in=self.cart.keys()).values_list('id', flat=True)
        )
        stale = [pid for pid in self.cart if pid not in still_visible]
        for pid in stale:
            del self.cart[pid]
        if stale:
            self.save()

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.current_price),
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        # Never let quantity exceed available stock
        if self.cart[product_id]['quantity'] > product.stock:
            self.cart[product_id]['quantity'] = product.stock
        if self.cart[product_id]['quantity'] < 1:
            self.cart[product_id]['quantity'] = 1

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.visible().filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[CART_SESSION_ID]
        self.save()
