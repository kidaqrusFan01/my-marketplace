from unittest import mock

from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import CustomUser
from products.models import Product, Category


def make_seller(username, approved=False, **extra):
    return CustomUser.objects.create_user(
        username=username, password='pass12345', email=f'{username}@example.com',
        is_seller=True, is_staff=True, store_name=f'{username} store', is_approved=approved, **extra
    )


def make_product(seller, name='Test Phone', **extra):
    category = Category.objects.get_or_create(name='Electronics')[0]
    return Product.objects.create(
        seller=seller, category=category, name=name, description='A product',
        price=50000, stock=5, is_active=True, **extra
    )


class RegistrationAlertTests(TestCase):
    """Requirement 1: the admin is notified about every registration."""

    def test_seller_registration_alerts_admin_and_starts_unapproved(self):
        resp = self.client.post(reverse('accounts:signup_seller'), {
            'username': 'newshop', 'email': 'shop@example.com', 'store_name': 'New Shop',
            'phone_number': '08011112222', 'password1': 'Str0ngPass!234', 'password2': 'Str0ngPass!234',
        })
        self.assertEqual(resp.status_code, 302)
        user = CustomUser.objects.get(username='newshop')
        self.assertTrue(user.is_seller)
        self.assertFalse(user.is_approved)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('approval needed', email.subject)
        self.assertIn('New Shop', email.subject)
        self.assertIn('newshop', email.body)
        self.assertIn('shop@example.com', email.body)
        self.assertIn(f'/admin/accounts/customuser/{user.pk}/change/', email.body)

    def test_customer_registration_alerts_admin_and_needs_no_approval(self):
        self.client.post(reverse('accounts:signup_customer'), {
            'username': 'buyer1', 'email': 'buyer@example.com',
            'password1': 'Str0ngPass!234', 'password2': 'Str0ngPass!234',
        })
        user = CustomUser.objects.get(username='buyer1')
        self.assertFalse(user.is_seller)
        self.assertTrue(user.is_approved)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('New customer registration', mail.outbox[0].subject)
        self.assertNotIn('ACTION NEEDED', mail.outbox[0].body)

    def test_failed_email_never_breaks_signup(self):
        with mock.patch('accounts.notifications.send_mail', side_effect=OSError('smtp down')):
            resp = self.client.post(reverse('accounts:signup_seller'), {
                'username': 'resilient', 'email': 'r@example.com', 'store_name': 'R Shop',
                'password1': 'Str0ngPass!234', 'password2': 'Str0ngPass!234',
            })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(username='resilient').exists())


class ProductVisibilityTests(TestCase):
    """Requirements 2 & 3: nothing from an unapproved seller is seen by shoppers."""

    def setUp(self):
        self.pending = make_seller('pendingshop', approved=False)
        self.approved = make_seller('goodshop', approved=True)
        self.hidden = make_product(self.pending, 'Hidden Gadget')
        self.shown = make_product(self.approved, 'Visible Gadget')
        self.shopper = Client()

    def test_hidden_everywhere_for_shoppers(self):
        home = self.shopper.get('/')
        self.assertContains(home, 'Visible Gadget')
        self.assertNotContains(home, 'Hidden Gadget')

        search = self.shopper.get('/', {'q': 'Gadget'})
        self.assertContains(search, 'Visible Gadget')
        self.assertNotContains(search, 'Hidden Gadget')

        self.assertEqual(self.shopper.get(self.hidden.get_absolute_url()).status_code, 404)
        self.assertEqual(self.shopper.get(self.shown.get_absolute_url()).status_code, 200)

    def test_cannot_add_hidden_product_to_cart(self):
        resp = self.shopper.post(reverse('cart:cart_add', args=[self.hidden.id]), {'quantity': 1})
        self.assertEqual(resp.status_code, 404)

    def test_hidden_from_other_logged_in_users_but_owner_can_preview(self):
        other = Client()
        other.force_login(self.approved)
        self.assertEqual(other.get(self.hidden.get_absolute_url()).status_code, 404)

        owner = Client()
        owner.force_login(self.pending)
        resp = owner.get(self.hidden.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Preview only')

    def test_hidden_product_cannot_be_deal_of_the_day(self):
        from datetime import timedelta
        from django.utils import timezone
        from products.models import DealOfTheDay
        now = timezone.now()
        DealOfTheDay.objects.create(product=self.hidden, deal_price=1000,
                                    starts_at=now - timedelta(hours=1), ends_at=now + timedelta(hours=1))
        self.assertIsNone(DealOfTheDay.get_current())
        self.assertNotContains(self.shopper.get('/'), 'Hidden Gadget')

    def test_seller_dashboard_tells_pending_seller_why(self):
        c = Client()
        c.force_login(self.pending)
        resp = c.get(reverse('products:seller_dashboard'))
        self.assertContains(resp, 'awaiting admin approval')
        self.assertContains(resp, 'Hidden Gadget')           # they still see their own products
        self.assertNotContains(resp, 'share-toggle')         # but no share links that would 404

    def test_cart_drops_product_when_approval_is_revoked(self):
        session_client = Client()
        session_client.post(reverse('cart:cart_add', args=[self.shown.id]), {'quantity': 2})
        self.assertContains(session_client.get(reverse('cart:cart_detail')), 'Visible Gadget')

        self.approved.is_approved = False
        self.approved.save()
        resp = session_client.get(reverse('cart:cart_detail'))
        self.assertNotContains(resp, 'Visible Gadget')


class AdminApprovalTests(TestCase):
    """Requirement 2: only an admin can authorize who is approved."""

    def setUp(self):
        self.admin = CustomUser.objects.create_superuser('boss', 'boss@example.com', 'pass12345')
        self.seller = make_seller('wannabe', approved=False)
        self.product = make_product(self.seller, 'Pending Item')
        self.changelist = reverse('admin:accounts_customuser_changelist')

    def _run_action(self, client, action):
        return client.post(self.changelist, {
            'action': action, '_selected_action': [self.seller.pk], 'index': 0,
        }, follow=True)

    def test_superuser_is_auto_approved(self):
        self.assertTrue(self.admin.is_approved)

    def test_admin_approves_then_product_appears_then_revoke_hides(self):
        shopper = Client()
        self.assertNotContains(shopper.get('/'), 'Pending Item')

        admin_client = Client()
        admin_client.force_login(self.admin)
        self._run_action(admin_client, 'approve_sellers')
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.is_approved)
        self.assertIsNotNone(self.seller.approved_at)
        self.assertContains(shopper.get('/'), 'Pending Item')

        self._run_action(admin_client, 'revoke_approval')
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_approved)
        self.assertNotContains(shopper.get('/'), 'Pending Item')

    def test_seller_cannot_use_admin_to_approve_anyone(self):
        other = make_seller('rival', approved=True)
        c = Client()
        c.force_login(other)  # an approved seller — staff, but no permission on users
        self.assertEqual(c.get(self.changelist).status_code, 403)
        self._run_action(c, 'approve_sellers')
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_approved)

    def test_seller_cannot_approve_themselves(self):
        c = Client()
        c.force_login(self.seller)
        c.post(reverse('accounts:profile'), {
            'first_name': 'A', 'last_name': 'B', 'email': self.seller.email,
            'phone_number': '', 'address': '', 'store_name': self.seller.store_name,
            'is_approved': 'on', 'is_superuser': 'on',
        })
        url = reverse('admin:accounts_customuser_change', args=[self.seller.pk])
        self.assertEqual(c.get(url).status_code, 403)
        self.assertEqual(c.post(url, {'is_approved': 'on'}).status_code, 403)
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_approved)
        self.assertFalse(self.seller.is_superuser)

    def test_admin_home_shows_pending_alert_with_count(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get('/admin/')
        self.assertContains(resp, 'awaiting your approval')
        self.assertContains(resp, '?approval=pending')
        self.assertEqual(resp.context['pending_approvals_count'], 1)

        self._run_action(c, 'approve_sellers')
        self.assertNotContains(c.get('/admin/'), 'awaiting your approval')

    def test_pending_filter_lists_only_pending_sellers(self):
        make_seller('already', approved=True)
        c = Client()
        c.force_login(self.admin)
        resp = c.get(self.changelist, {'approval': 'pending'})
        self.assertContains(resp, 'wannabe')
        self.assertNotContains(resp, '>already<')

    def test_alert_is_not_computed_for_regular_visitors(self):
        resp = Client().get('/')
        self.assertEqual(resp.context['pending_approvals_count'], 0)
        self.assertNotContains(resp, 'nav-pending-badge')


class GrandfatheringTests(TestCase):
    def test_migration_helper_approves_existing_users(self):
        """Everyone registered before this feature existed must be approved,
        so current sellers' products don't vanish after upgrading."""
        import importlib
        from django.apps import apps
        migration = importlib.import_module('accounts.migrations.0005_user_approval')
        old = make_seller('legacy', approved=False)
        migration.approve_existing_users(apps, None)
        old.refresh_from_db()
        self.assertTrue(old.is_approved)
