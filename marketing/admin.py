from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Advertisement, BusinessInquiry, VendorSubscription, VendorPlanRequest


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


@admin.register(VendorSubscription)
class VendorSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('seller', 'current_plan', 'activated_at', 'updated_at')
    list_filter = ('current_plan',)
    search_fields = ('seller__username', 'seller__store_name')


@admin.register(VendorPlanRequest)
class VendorPlanRequestAdmin(admin.ModelAdmin):
    list_display = ('seller', 'requested_plan', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'requested_plan')
    search_fields = ('seller__username', 'seller__store_name')
    actions = ['confirm_and_activate', 'reject_request']

    @admin.action(description="Confirm payment & activate the requested plan")
    def confirm_and_activate(self, request, queryset):
        activated = 0
        for plan_request in queryset.filter(status='pending'):
            subscription = VendorSubscription.get_or_create_for(plan_request.seller)
            subscription.current_plan = plan_request.requested_plan
            subscription.activated_at = timezone.now()
            subscription.save(update_fields=['current_plan', 'activated_at'])

            plan_request.status = 'confirmed'
            plan_request.processed_at = timezone.now()
            plan_request.save(update_fields=['status', 'processed_at'])
            activated += 1
        self.message_user(request, f"Activated {activated} plan(s).")

    @admin.action(description="Reject request (no changes to seller's plan)")
    def reject_request(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected', processed_at=timezone.now())
        self.message_user(request, f"Rejected {updated} request(s).")
