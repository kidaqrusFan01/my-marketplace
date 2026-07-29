def loyalty_balance(request):
    """Makes the logged-in user's loyalty point balance available in every
    template (for the small coin badge in the navbar)."""
    if not request.user.is_authenticated:
        return {'loyalty_points_balance': None}
    from .models import LoyaltyAccount
    account = LoyaltyAccount.objects.filter(user=request.user).only('balance').first()
    return {'loyalty_points_balance': account.balance if account else 0}
