import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model for Corazon Marketplace.
    Adds a seller flag so a user can register as a seller and gain
    access to the seller admin area to upload/manage their own products.
    """
    is_seller = models.BooleanField(
        default=False,
        help_text="Designates whether this user can sell products on the marketplace."
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    store_name = models.CharField(
        max_length=100, blank=True,
        help_text="Public store name shown to buyers (sellers only)."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Every user (customer or seller) gets a short unique code so they can
    # share products with a personal referral link, e.g. /product/x/?ref=AB12CD9F.
    # Anyone who completes a purchase after following that link earns the
    # code's owner loyalty points — see the `loyalty` app.
    referral_code = models.CharField(max_length=12, unique=True, blank=True, db_index=True)

    # Who referred this user, captured from ?ref=<code> at signup time (see
    # accounts.middleware.ReferralTrackingMiddleware). Purchase-based loyalty
    # bonuses to the referrer are awarded in orders.views, not here — we
    # don't reward the signup itself, only real purchases, to avoid fake
    # signups being used to farm points.
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_unique_referral_code()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_unique_referral_code(cls):
        while True:
            code = secrets.token_hex(4).upper()  # 8 hex chars, e.g. 'A1B2C3D4'
            if not cls.objects.filter(referral_code=code).exists():
                return code

    def __str__(self):
        return self.username
