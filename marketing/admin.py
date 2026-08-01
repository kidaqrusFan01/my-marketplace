from django.contrib import admin
from django.utils.html import format_html
from .models import Advertisement, BusinessInquiry


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'advertiser_name', 'preview', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:36px;border-radius:4px;">', obj.image.url)
        return "(no image)"
    preview.short_description = "Preview"


@admin.register(BusinessInquiry)
class BusinessInquiryAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'inquiry_type', 'contact_name', 'email', 'status', 'created_at')
    list_filter = ('inquiry_type', 'status')
    search_fields = ('company_name', 'contact_name', 'email')
    list_editable = ('status',)
