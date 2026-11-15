from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    A small in-site alert for one user (shown under the bell in the nav and
    on /notifications/). Currently used to tell a seller that someone ordered
    their product; kept generic so other alert types can reuse it later.
    """
    KIND_CHOICES = [
        ('order_received', 'Order received'),
        ('shared_product_ordered', 'Shared product ordered'),
        ('general', 'General'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=300, blank=True, help_text="Where clicking the alert should go.")
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"
