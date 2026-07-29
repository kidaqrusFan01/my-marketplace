from django.contrib import admin
from django.utils import timezone

from .models import LoyaltyAccount, LoyaltyTransaction, RedemptionRequest


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'lifetime_earned', 'lifetime_redeemed', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('lifetime_earned', 'lifetime_redeemed', 'updated_at')


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'points', 'reason', 'related_order', 'related_product', 'created_at')
    list_filter = ('reason',)
    search_fields = ('account__user__username',)
    # Transactions are an append-only ledger — created via LoyaltyAccount.award()/.redeem()
    # so the balance can never drift from its history. Admin can view but not hand-edit them.
    readonly_fields = [f.name for f in LoyaltyTransaction._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RedemptionRequest)
class RedemptionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'redemption_type', 'points_used', 'naira_value', 'status', 'created_at')
    list_filter = ('status', 'redemption_type')
    search_fields = ('user__username', 'phone_number', 'bank_details')
    actions = ['mark_completed', 'mark_rejected_and_refund']

    @admin.action(description="Mark selected requests as completed")
    def mark_completed(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='completed', processed_at=timezone.now())
        self.message_user(request, f"{updated} request(s) marked completed.")

    @admin.action(description="Reject selected requests and refund points")
    def mark_rejected_and_refund(self, request, queryset):
        count = 0
        for redemption in queryset.filter(status='pending'):
            redemption.mark_rejected_and_refund()
            count += 1
        self.message_user(request, f"{count} request(s) rejected and refunded.")
