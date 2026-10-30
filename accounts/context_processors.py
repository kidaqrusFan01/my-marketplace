def pending_approvals(request):
    """
    Number of seller registrations still waiting for admin approval — shown
    as an alert banner on the admin home page and as a badge on the site's
    "Admin" link. Only computed for superusers (one cheap COUNT query), so
    ordinary visitors never pay for it.
    """
    user = getattr(request, 'user', None)
    if not (user and user.is_authenticated and user.is_superuser):
        return {'pending_approvals_count': 0}
    from .models import CustomUser
    return {
        'pending_approvals_count': CustomUser.objects.filter(is_seller=True, is_approved=False).count()
    }
