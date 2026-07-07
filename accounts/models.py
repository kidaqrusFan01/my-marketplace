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

    def __str__(self):
        return self.username
