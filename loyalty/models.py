from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from . import constants


class LoyaltyAccount(models.Model):
    """
    One per user (customer or seller). Holds the current spendable balance.
    Never edit `balance` directly — always go through LoyaltyAccount.award()
    or .redeem() so a matching LoyaltyTransaction is always written and the
    balance can never drift from its own history.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loyalty_account'
    )
    balance = models.PositiveIntegerField(default=0)
    lifetime_earned = models.PositiveIntegerField(default=0)
    lifetime_redeemed = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.balance} pts"

    @classmethod
    def get_or_create_for(cls, user):
        account, _ = cls.objects.get_or_create(user=user)
        return account

    @transaction.atomic
    def award(self, points, reason, related_order=None, related_product=None, note=""):
        """Credits points and logs why. `points` must be > 0."""
        if points <= 0:
            return None
        account = LoyaltyAccount.objects.select_for_update().get(pk=self.pk)
        account.balance += points
        account.lifetime_earned += points
        account.save(update_fields=['balance', 'lifetime_earned', 'updated_at'])
        self.balance = account.balance
        self.lifetime_earned = account.lifetime_earned
        return LoyaltyTransaction.objects.create(
            account=account, points=points, reason=reason,
            related_order=related_order, related_product=related_product, note=note,
        )

    @transaction.atomic
    def redeem(self, points, reason, related_order=None, note=""):
        """
        Debits points and logs why. Returns the LoyaltyTransaction, or None
        if the account doesn't have enough balance (caller should check
        `account.balance` before offering a redemption option anyway, but
        this guards against race conditions / stale page state too).
        """
        if points <= 0:
            return None
        account = LoyaltyAccount.objects.select_for_update().get(pk=self.pk)
        if account.balance < points:
            return None
        account.balance -= points
        account.lifetime_redeemed += points
        account.save(update_fields=['balance', 'lifetime_redeemed', 'updated_at'])
        self.balance = account.balance
        self.lifetime_redeemed = account.lifetime_redeemed
        return LoyaltyTransaction.objects.create(
            account=account, points=-points, reason=reason,
            related_order=related_order, note=note,
        )


class LoyaltyTransaction(models.Model):
    REASON_CHOICES = [
        ('purchase', 'Purchase'),
        ('deal_of_day_purchase_bonus', 'Deal of the Day purchase bonus'),
        ('share', 'Shared a product'),
        ('referral_purchase', 'Referral led to a purchase'),
        ('new_buyer_bonus', 'Referral brought in a new buyer'),
        ('redeemed_discount', 'Redeemed for order discount'),
        ('redeemed_delivery', 'Redeemed for delivery fee'),
        ('redeemed_airtime', 'Redeemed for airtime'),
        ('redeemed_data', 'Redeemed for data bundle'),
        ('redeemed_cash', 'Redeemed for cash payout'),
        ('admin_adjustment', 'Manual adjustment by admin'),
    ]

    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    points = models.IntegerField(help_text="Positive = earned, negative = redeemed.")
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    related_order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='loyalty_transactions'
    )
    related_product = models.ForeignKey(
        'products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='loyalty_transactions'
    )
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = "+" if self.points >= 0 else ""
        return f"{self.account.user.username}: {sign}{self.points} ({self.get_reason_display()})"


class RedemptionRequest(models.Model):
    """
    A request to convert loyalty points into airtime, a mobile data bundle,
    or a cash payout. Points are deducted immediately when the request is
    submitted (so the balance shown is always accurate), and the request
    sits as 'pending' until a staff member fulfills it manually from the
    admin — this project doesn't integrate a live telco/bank API, so
    fulfillment is a real person acting on this queue, the same way a
    small business would before automating.
    """
    TYPE_CHOICES = [
        ('airtime', 'Airtime'),
        ('data', 'Data bundle'),
        ('cash', 'Cash payout (bank transfer)'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected (points refunded)'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='redemption_requests')
    redemption_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    points_used = models.PositiveIntegerField()
    naira_value = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=20, blank=True, help_text="Required for airtime/data.")
    bank_details = models.CharField(max_length=200, blank=True, help_text="Required for cash payout.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.get_redemption_type_display()} ({self.points_used} pts)"

    def mark_rejected_and_refund(self):
        """Staff-facing helper: reject a request and give the points back."""
        if self.status == 'rejected':
            return
        account = LoyaltyAccount.get_or_create_for(self.user)
        account.award(
            self.points_used, reason='admin_adjustment',
            note=f"Refund for rejected {self.get_redemption_type_display()} request #{self.pk}"
        )
        self.status = 'rejected'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
