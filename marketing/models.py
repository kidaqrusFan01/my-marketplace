from django.db import models


class Advertisement(models.Model):
    """
    A featured ad banner shown as a "site break" partway down the homepage
    (between Featured Products and the main catalog grid) — this is the
    inventory that the /advertise/ page invites businesses to buy space in.

    If there's exactly one active ad it displays as a static banner; if
    there are two or more, the homepage auto-scrolls through them. Either
    way nothing breaks if there are zero — the section just doesn't render.
    """
    title = models.CharField(max_length=150)
    image = models.ImageField(
        upload_to='advertisements/',
        help_text="Wide banner image works best (recommended around 1000x250)."
    )
    link_url = models.URLField(
        blank=True,
        help_text="Where clicking the ad should take shoppers. Leave blank for a non-clickable banner."
    )
    advertiser_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        is_new_upload = bool(self.image) and not self.image._committed
        super().save(*args, **kwargs)
        if is_new_upload:
            from products.image_utils import optimize_image_field
            original_name = self.image.name
            if optimize_image_field(self.image, filename_hint=original_name, max_dimension=(1600, 500)):
                super().save(update_fields=['image'])

    def __str__(self):
        return self.title


class BusinessInquiry(models.Model):
    """
    Lead capture for the /advertise/ page — covers both "I want to
    advertise a banner on the site" and "I want to post jobs through your
    careers page" inquiries (the recruitment-page banner routes here too),
    since both are fundamentally the same thing: a business asking to pay
    Corazon Marketplace for placement. A staff member follows up manually;
    this project doesn't wire up a live payment/invoicing flow for ad
    sales, same reasoning as the loyalty cash payouts — that needs a real
    billing system behind it, not something to fake.
    """
    INQUIRY_TYPE_CHOICES = [
        ('advertising', 'Advertise a banner on the site'),
        ('job_posting', 'Post jobs on the Careers page'),
        ('other', 'Something else'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('closed', 'Closed'),
    ]

    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES, default='advertising')
    company_name = models.CharField(max_length=150)
    contact_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Business inquiries"

    def __str__(self):
        return f"{self.company_name} — {self.get_inquiry_type_display()}"
