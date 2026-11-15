def unread_notifications(request):
    """Unread alert count for the bell badge in the nav (logged-in users only)."""
    user = getattr(request, 'user', None)
    if not (user and user.is_authenticated):
        return {'unread_notifications_count': 0}
    from .models import Notification
    return {
        'unread_notifications_count': Notification.objects.filter(recipient=user, is_read=False).count()
    }
