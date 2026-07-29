from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Review, HeroBanner, DealOfTheDay


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price', 'discount_price', 'stock', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description', 'seller__username')
    inlines = [ProductImageInline]

    def get_queryset(self, request):
        """
        Sellers only ever see and manage their OWN products in the admin.
        Superusers and regular (non-seller) staff members see everything.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser or not request.user.is_seller:
            return qs
        return qs.filter(seller=request.user)

    def save_model(self, request, obj, form, change):
        if request.user.is_seller and not request.user.is_superuser and not obj.pk:
            obj.seller = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj is not None and request.user.is_seller and not request.user.is_superuser:
            return obj.seller_id == request.user.id
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and request.user.is_seller and not request.user.is_superuser:
            return obj.seller_id == request.user.id
        return super().has_delete_permission(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """Hide the 'seller' field from sellers editing in admin — it's set automatically."""
        form = super().get_form(request, obj, **kwargs)
        if request.user.is_seller and not request.user.is_superuser and 'seller' in form.base_fields:
            del form.base_fields['seller']
        return form


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    """
    Platform-level (superuser) tool for managing the homepage rotating
    banner. Not exposed to sellers — only Product/ProductImage permissions
    are ever granted to seller accounts.
    """
    list_display = ('title', 'preview', 'category', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    fields = ('title', 'eyebrow', 'subtitle', 'cta_text', 'category',
              'image', 'placeholder_style', 'order', 'is_active')

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;">', obj.image.url)
        return "(no image — using placeholder)"
    preview.short_description = "Image"


@admin.register(DealOfTheDay)
class DealOfTheDayAdmin(admin.ModelAdmin):
    list_display = ('product', 'deal_price', 'starts_at', 'ends_at', 'status', 'is_active')
    list_filter = ('is_active',)
    autocomplete_fields = []
    search_fields = ('product__name',)

    def status(self, obj):
        if not obj.is_active:
            return "Inactive"
        now = timezone.now()
        if now < obj.starts_at:
            return "Upcoming"
        if now > obj.ends_at:
            return "Ended"
        return "🔴 LIVE NOW"
    status.short_description = "Status"
