from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from .models import CustomUser


class ApprovalStatusFilter(admin.SimpleListFilter):
    """Quick access to the approval queue: 'Pending sellers' is what the
    admin banner and the storefront nav badge link to."""
    title = 'seller approval'
    parameter_name = 'approval'

    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending sellers (awaiting approval)'),
            ('approved', 'Approved sellers'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(is_seller=True, is_approved=False)
        if self.value() == 'approved':
            return queryset.filter(is_seller=True, is_approved=True)
        return queryset


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'store_name', 'is_seller', 'approval_status', 'date_joined', 'is_staff', 'is_active')
    list_filter = (ApprovalStatusFilter, 'is_seller', 'is_agent', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'store_name')
    ordering = ('-date_joined',)
    readonly_fields = ('approved_at',)
    fieldsets = UserAdmin.fieldsets + (
        ('Marketplace Info', {'fields': ('is_seller', 'is_agent', 'phone_number', 'address', 'store_name')}),
        ('Admin Approval', {
            'fields': ('is_approved', 'approved_at'),
            'description': "A seller's products are hidden from shoppers until this is ticked.",
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Marketplace Info', {'fields': ('is_seller', 'email', 'store_name')}),
        ('Admin Approval', {'fields': ('is_approved',)}),
    )
    actions = ['approve_sellers', 'revoke_approval']

    @admin.display(description='Approval', ordering='is_approved')
    def approval_status(self, obj):
        if not obj.is_seller:
            return '—'
        return '✅ Approved' if obj.is_approved else '⏳ Pending'

    def save_model(self, request, obj, form, change):
        # Keep approved_at honest when approval is toggled from the edit form.
        if 'is_approved' in form.changed_data:
            obj.approved_at = timezone.now() if obj.is_approved else None
        super().save_model(request, obj, form, change)

    # `permissions=['change']` makes Django deny these actions for anyone
    # without the "change user" permission. Sellers are staff (so they can
    # manage their own products in /admin/) but are never granted any
    # permission on user accounts — so only admins can ever approve.
    @admin.action(description='Approve selected sellers (show their products)', permissions=['change'])
    def approve_sellers(self, request, queryset):
        updated = queryset.filter(is_seller=True, is_approved=False).update(
            is_approved=True, approved_at=timezone.now()
        )
        self.message_user(request, f"Approved {updated} seller(s). Their products are now visible to shoppers.",
                          messages.SUCCESS)

    @admin.action(description='Revoke approval (hide their products again)', permissions=['change'])
    def revoke_approval(self, request, queryset):
        updated = queryset.filter(is_seller=True, is_approved=True, is_superuser=False).update(
            is_approved=False, approved_at=None
        )
        self.message_user(request, f"Revoked approval for {updated} seller(s). Their products are hidden.",
                          messages.WARNING)
