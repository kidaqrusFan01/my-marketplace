from unittest import mock

from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import CustomUser
from accounts.tests import make_seller, make_product
from notifications.models import Notification
from orders.models import Order

SHIPPING = {
    'full_name': 'Ngozi Buyer', 'email': 'ngozi@example.com',
    'address': '12 Allen Avenue', 'city': 'Ikeja', 'postal_code': '100271',
    'phone_number': '08099998888',
}


def make_buyer(username='ngozi'):
    return CustomUser.objects.create_user(
        username=username, password='pass12345', email=f'{username}@example.com', is_approved=True
    )


def place_order(buyer, *product_qty):
    """Log in as buyer, add (product, qty) pairs to the cart, and check out."""
    client = Client()
    client.force_login(buyer)
    for product, qty in product_qty:
        client.post(reverse('cart:cart_add', args=[product.id]), {'quantity': qty})
    return client, client.post(reverse('orders:order_create'), SHIPPING)


class SellerOrderAlertTests(TestCase):
    def setUp(self):
        self.seller = make_seller('wax_queen', approved=True)
        self.phone = make_product(self.seller, 'Ankara Wax Print')
        self.buyer = make_buyer()

    def test_seller_is_alerted_in_site_and_by_email_when_order_is_placed(self):
        _, resp = place_order(self.buyer, (self.phone, 2))
        self.assertEqual(resp.status_code, 302)
        order = Order.objects.get()

        n = Notification.objects.get(recipient=self.seller)
        self.assertEqual(n.kind, 'order_received')
        self.assertFalse(n.is_read)
        self.assertIn(f'#{order.pk}', n.title)
        self.assertIn('Ankara Wax Print', n.title)
        self.assertIn('2 × Ankara Wax Print', n.message)
        self.assertIn('₦100,000.00', n.message)
        self.assertEqual(n.url, reverse('orders:seller_orders'))

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.seller.email])
        self.assertIn(f'#{order.pk}', email.subject)
        self.assertIn('2 × Ankara Wax Print', email.body)
        self.assertIn('₦100,000.00', email.body)
        self.assertIn(reverse('orders:seller_orders'), email.body)

    def test_email_keeps_buyer_contact_details_private(self):
        place_order(self.buyer, (self.phone, 1))
        body = mail.outbox[0].body
        for private in ('12 Allen Avenue', '08099998888', 'ngozi@example.com', 'Ngozi Buyer'):
            self.assertNotIn(private, body)

    def test_no_alert_until_an_order_is_actually_placed(self):
        client = Client()
        client.force_login(self.buyer)
        client.post(reverse('cart:cart_add', args=[self.phone.id]), {'quantity': 1})
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        bad = dict(SHIPPING, email='not-an-email')          # checkout form fails validation
        client.post(reverse('orders:order_create'), bad)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_buyer_is_not_alerted_about_their_own_purchase(self):
        place_order(self.buyer, (self.phone, 1))
        self.assertEqual(Notification.objects.filter(recipient=self.buyer).count(), 0)
        self.assertNotIn(self.buyer.email, [a for m in mail.outbox for a in m.to])

    def test_seller_without_email_still_gets_the_in_site_alert(self):
        CustomUser.objects.filter(pk=self.seller.pk).update(email='')
        place_order(self.buyer, (self.phone, 1))
        self.assertEqual(Notification.objects.filter(recipient=self.seller).count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_outage_never_breaks_checkout(self):
        with mock.patch('orders.notifications.send_mail', side_effect=OSError('smtp down')):
            _, resp = place_order(self.buyer, (self.phone, 1))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.seller).count(), 1)

    def test_seller_ordering_their_own_product_is_not_alerted(self):
        place_order(self.seller, (self.phone, 1))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)


class MultiSellerOrderTests(TestCase):
    def setUp(self):
        self.a = make_seller('seller_a', approved=True)
        self.b = make_seller('seller_b', approved=True)
        self.a1 = make_product(self.a, 'Alpha Shoes')
        self.a2 = make_product(self.a, 'Alpha Bag')
        self.b1 = make_product(self.b, 'Beta Watch')
        self.buyer = make_buyer()

    def test_each_seller_gets_exactly_one_alert_listing_only_their_items(self):
        place_order(self.buyer, (self.a1, 1), (self.a2, 3), (self.b1, 1))

        na = Notification.objects.get(recipient=self.a)
        self.assertIn('2 of your products', na.title)
        self.assertIn('Alpha Shoes', na.message)
        self.assertIn('3 × Alpha Bag', na.message)
        self.assertNotIn('Beta Watch', na.message)

        nb = Notification.objects.get(recipient=self.b)
        self.assertIn('Beta Watch', nb.title)
        self.assertNotIn('Alpha', nb.message)

        self.assertEqual(len(mail.outbox), 2)
        by_recipient = {m.to[0]: m for m in mail.outbox}
        self.assertIn('Alpha Bag', by_recipient[self.a.email].body)
        self.assertNotIn('Beta Watch', by_recipient[self.a.email].body)
        self.assertNotIn('Alpha', by_recipient[self.b.email].body)

    def test_seller_orders_page_shows_only_own_items_and_delivery_details(self):
        place_order(self.buyer, (self.a1, 1), (self.b1, 2))
        c = Client()
        c.force_login(self.a)
        resp = c.get(reverse('orders:seller_orders'))
        self.assertContains(resp, 'Alpha Shoes')
        self.assertNotContains(resp, 'Beta Watch')
        self.assertContains(resp, '12 Allen Avenue')
        self.assertContains(resp, '08099998888')

    def test_orders_page_is_for_sellers_only(self):
        place_order(self.buyer, (self.a1, 1))
        anon = Client().get(reverse('orders:seller_orders'))
        self.assertEqual(anon.status_code, 302)
        self.assertIn('/accounts/login/', anon['Location'])

        shopper = Client()
        shopper.force_login(self.buyer)
        resp = shopper.get(reverse('orders:seller_orders'), follow=True)
        self.assertNotContains(resp, 'Orders Received')       # bounced to seller signup, not shown the page


class NotificationInboxTests(TestCase):
    def setUp(self):
        self.seller = make_seller('inbox_seller', approved=True)
        self.other = make_seller('someone_else', approved=True)
        self.product = make_product(self.seller, 'Inbox Item')
        place_order(CustomUser.objects.create_user('b1', password='x', email='b1@x.com', is_approved=True),
                    (self.product, 1))

    def test_bell_shows_unread_count_then_clears_after_viewing(self):
        c = Client()
        c.force_login(self.seller)
        home = c.get('/')
        self.assertEqual(home.context['unread_notifications_count'], 1)
        self.assertContains(home, 'notif-badge')

        page = c.get(reverse('notifications:list'))
        self.assertContains(page, 'Inbox Item')
        self.assertContains(page, 'notification-item--unread')    # still highlighted on first view

        again = c.get(reverse('notifications:list'))
        self.assertNotContains(again, 'notification-item--unread')
        self.assertEqual(c.get('/').context['unread_notifications_count'], 0)

    def test_people_only_see_their_own_notifications(self):
        c = Client()
        c.force_login(self.other)
        self.assertEqual(c.get('/').context['unread_notifications_count'], 0)
        self.assertNotContains(c.get(reverse('notifications:list')), 'Inbox Item')

    def test_notifications_require_login(self):
        resp = Client().get(reverse('notifications:list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp['Location'])
