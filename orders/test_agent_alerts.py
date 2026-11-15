from unittest import mock

from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import CustomUser
from accounts.tests import make_seller, make_product
from agents.models import AgentProfile
from notifications.models import Notification
from orders.models import Order
from orders.tests import make_buyer, SHIPPING


def make_agent(username, email=True, is_agent=True):
    user = CustomUser.objects.create_user(
        username=username, password='pass12345',
        email=f'{username}@example.com' if email else '', is_approved=True, is_agent=is_agent,
    )
    if is_agent:
        AgentProfile.objects.create(user=user, display_name=f'{username.title()} Promotions')
    return user


def agent_shares(agent, product):
    c = Client()
    c.force_login(agent)
    resp = c.post(reverse('loyalty:track_share', args=[product.id]))
    assert resp.json()['awarded'], "share should have been recorded"


def checkout(buyer, products, ref_code=None):
    """Customer (optionally arriving through a ?ref= link) buys [(product, qty), ...]."""
    c = Client()
    c.force_login(buyer)
    if ref_code:
        c.get(products[0][0].get_absolute_url(), {'ref': ref_code})     # clicks the shared link
    for product, qty in products:
        c.post(reverse('cart:cart_add', args=[product.id]), {'quantity': qty})
    return c.post(reverse('orders:order_create'), SHIPPING)


def agent_alerts(agent):
    return Notification.objects.filter(recipient=agent, kind='shared_product_ordered')


class SharedProductOrderedTests(TestCase):
    def setUp(self):
        self.seller = make_seller('wax_queen', approved=True)
        self.shared = make_product(self.seller, 'Ankara Wax Print')
        self.other = make_product(self.seller, 'Plain Cotton')
        self.agent = make_agent('promo_pete')
        self.buyer = make_buyer()
        agent_shares(self.agent, self.shared)

    def test_agent_is_alerted_in_site_and_by_email_when_their_link_leads_to_an_order(self):
        resp = checkout(self.buyer, [(self.shared, 2)], ref_code=self.agent.referral_code)
        self.assertEqual(resp.status_code, 302)

        n = agent_alerts(self.agent).get()
        self.assertFalse(n.is_read)
        self.assertIn('Ankara Wax Print', n.title)
        self.assertIn('2 × Ankara Wax Print', n.message)
        self.assertIn('₦100,000.00', n.message)
        self.assertEqual(n.url, reverse('agents:page'))

        agent_mail = [m for m in mail.outbox if m.to == [self.agent.email]]
        self.assertEqual(len(agent_mail), 1)
        self.assertIn('Promo_Pete Promotions', agent_mail[0].body)
        self.assertIn('2 × Ankara Wax Print', agent_mail[0].body)
        self.assertIn(reverse('agents:page'), agent_mail[0].body)

    def test_alert_carries_no_buyer_details(self):
        checkout(self.buyer, [(self.shared, 1)], ref_code=self.agent.referral_code)
        n = agent_alerts(self.agent).get()
        text = n.title + n.message + [m for m in mail.outbox if m.to == [self.agent.email]][0].body
        for private in ('12 Allen Avenue', '08099998888', 'ngozi@example.com', 'Ngozi Buyer', 'Ikeja', 'ngozi'):
            self.assertNotIn(private, text)

    def test_seller_still_gets_their_own_order_alert(self):
        checkout(self.buyer, [(self.shared, 1)], ref_code=self.agent.referral_code)
        self.assertEqual(Notification.objects.filter(recipient=self.seller, kind='order_received').count(), 1)
        self.assertEqual(agent_alerts(self.agent).count(), 1)

    def test_no_alert_if_the_customer_did_not_come_through_the_agents_link(self):
        checkout(self.buyer, [(self.shared, 1)])            # bought it directly, no ref link
        self.assertEqual(agent_alerts(self.agent).count(), 0)
        self.assertFalse([m for m in mail.outbox if m.to == [self.agent.email]])

    def test_only_items_the_agent_shared_are_mentioned(self):
        checkout(self.buyer, [(self.shared, 1), (self.other, 3)], ref_code=self.agent.referral_code)
        n = agent_alerts(self.agent).get()
        self.assertIn('Ankara Wax Print', n.message)
        self.assertNotIn('Plain Cotton', n.message)

    def test_no_alert_when_the_order_has_nothing_the_agent_shared(self):
        checkout(self.buyer, [(self.other, 1)], ref_code=self.agent.referral_code)
        self.assertEqual(agent_alerts(self.agent).count(), 0)

    def test_only_the_agent_whose_link_was_used_is_alerted(self):
        rival = make_agent('rival_agent')
        agent_shares(rival, self.shared)                     # rival shared the same product too
        checkout(self.buyer, [(self.shared, 1)], ref_code=self.agent.referral_code)
        self.assertEqual(agent_alerts(self.agent).count(), 1)
        self.assertEqual(agent_alerts(rival).count(), 0)

    def test_agent_is_alerted_for_a_customer_who_signed_up_through_their_link(self):
        referred = make_buyer('referred_buyer')
        referred.referred_by = self.agent
        referred.save()
        checkout(referred, [(self.shared, 1)])               # no ref in this session, but signed up via the agent
        self.assertEqual(agent_alerts(self.agent).count(), 1)

    def test_one_alert_even_if_both_attribution_routes_point_at_the_same_agent(self):
        referred = make_buyer('doubly_referred')
        referred.referred_by = self.agent
        referred.save()
        checkout(referred, [(self.shared, 1)], ref_code=self.agent.referral_code)
        self.assertEqual(agent_alerts(self.agent).count(), 1)

    def test_nothing_before_an_order_is_actually_placed(self):
        c = Client()
        c.force_login(self.buyer)
        c.get(self.shared.get_absolute_url(), {'ref': self.agent.referral_code})
        c.post(reverse('cart:cart_add', args=[self.shared.id]), {'quantity': 1})
        self.assertEqual(agent_alerts(self.agent).count(), 0)


class SharedProductOrderedEdgeCases(TestCase):
    def setUp(self):
        self.seller = make_seller('shop_owner', approved=True)
        self.product = make_product(self.seller, 'Edge Item')
        self.buyer = make_buyer()

    def test_sharer_who_is_not_an_agent_is_not_alerted(self):
        plain = make_agent('plain_sharer', is_agent=False)
        agent_shares(plain, self.product)
        checkout(self.buyer, [(self.product, 1)], ref_code=plain.referral_code)
        self.assertEqual(agent_alerts(plain).count(), 0)

    def test_agent_buying_through_their_own_link_is_not_alerted(self):
        agent = make_agent('self_buyer')
        agent_shares(agent, self.product)
        checkout(agent, [(self.product, 1)], ref_code=agent.referral_code)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(agent_alerts(agent).count(), 0)

    def test_agent_who_is_also_the_seller_gets_only_the_seller_alert(self):
        CustomUser.objects.filter(pk=self.seller.pk).update(is_agent=True)
        self.seller.refresh_from_db()
        AgentProfile.objects.create(user=self.seller, display_name='Shop Agent')
        agent_shares(self.seller, self.product)
        checkout(self.buyer, [(self.product, 1)], ref_code=self.seller.referral_code)
        self.assertEqual(agent_alerts(self.seller).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.seller, kind='order_received').count(), 1)

    def test_agent_without_email_still_gets_the_in_site_alert(self):
        agent = make_agent('no_email_agent', email=False)
        agent_shares(agent, self.product)
        checkout(self.buyer, [(self.product, 1)], ref_code=agent.referral_code)
        self.assertEqual(agent_alerts(agent).count(), 1)
        self.assertFalse([m for m in mail.outbox if '' in m.to])

    def test_email_outage_never_breaks_checkout(self):
        agent = make_agent('resilient_agent')
        agent_shares(agent, self.product)
        with mock.patch('orders.notifications.send_mail', side_effect=OSError('smtp down')):
            resp = checkout(self.buyer, [(self.product, 1)], ref_code=agent.referral_code)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(agent_alerts(agent).count(), 1)

    def test_a_bad_ref_code_is_ignored(self):
        agent = make_agent('real_agent')
        agent_shares(agent, self.product)
        resp = checkout(self.buyer, [(self.product, 1)], ref_code='ZZZZZZZZ')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(agent_alerts(agent).count(), 0)

    def test_agent_sees_the_alert_under_their_bell(self):
        agent = make_agent('bell_agent')
        agent_shares(agent, self.product)
        checkout(self.buyer, [(self.product, 1)], ref_code=agent.referral_code)
        c = Client()
        c.force_login(agent)
        self.assertContains(c.get('/'), 'notif-badge')
        self.assertContains(c.get(reverse('notifications:list')), 'you shared')
