from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(
        max_length=50, blank=True,
        help_text="Optional emoji or short code shown next to the category name."
    )

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='products', limit_choices_to={'is_seller': True}
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Optional sale price, shown crossed out original price if set."
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Detect a brand-new file upload (as opposed to re-saving an instance
        # whose image was already processed and committed to storage).
        is_new_upload = bool(self.image) and not self.image._committed

        super().save(*args, **kwargs)

        if is_new_upload:
            from .image_utils import optimize_image_field
            original_name = self.image.name
            if optimize_image_field(self.image, filename_hint=original_name):
                super().save(update_fields=['image'])

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def in_stock(self):
        return self.stock > 0

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """Additional gallery images for a product (beyond the main image)."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')

    def save(self, *args, **kwargs):
        is_new_upload = bool(self.image) and not self.image._committed
        super().save(*args, **kwargs)
        if is_new_upload:
            from .image_utils import optimize_image_field
            original_name = self.image.name
            if optimize_image_field(self.image, filename_hint=original_name):
                super().save(update_fields=['image'])

    def __str__(self):
        return f"Image for {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"


class HeroBanner(models.Model):
    """
    A single slide in the homepage rotating hero carousel.
    Upload a real photo here (Django admin -> Hero Banners) and it replaces
    the illustrated placeholder automatically — no code/template edits
    needed. If no image is uploaded, the slide falls back to a gradient +
    icon placeholder so the carousel is never literally blank.
    """
    title = models.CharField(max_length=100, help_text="Big headline text, e.g. 'Level Up Your Setup'")
    eyebrow = models.CharField(
        max_length=60, blank=True,
        help_text="Small label above the title, e.g. 'Tech Deals'"
    )
    subtitle = models.CharField(max_length=200, blank=True)
    cta_text = models.CharField(max_length=50, default="Shop Now")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Clicking the slide's button takes shoppers to this category."
    )
    image = models.ImageField(
        upload_to='hero_banners/', blank=True, null=True,
        help_text="Recommended: a wide landscape photo (at least 1600x600). "
                   "It will be automatically resized/optimized and cropped to fill the banner."
    )
    # Used only when no image is uploaded, so the slide still looks intentional.
    PLACEHOLDER_STYLE_CHOICES = [
        ('electronics', 'Electronics (dark blue)'),
        ('fashion', 'Fashion (purple)'),
        ('home', 'Home & Kitchen (teal/green)'),
        ('sports', 'Sports & Outdoors (orange/pink)'),
        ('books', 'Books (blue/green)'),
    ]
    placeholder_style = models.CharField(
        max_length=20, choices=PLACEHOLDER_STYLE_CHOICES, default='electronics'
    )
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        is_new_upload = bool(self.image) and not self.image._committed
        super().save(*args, **kwargs)
        if is_new_upload:
            from .image_utils import optimize_image_field
            original_name = self.image.name
            # Hero banners are wide, so give them a bigger max size than the
            # square product-thumbnail default.
            if optimize_image_field(self.image, filename_hint=original_name, max_dimension=(1920, 1080)):
                super().save(update_fields=['image'])

    def __str__(self):
        return self.title
