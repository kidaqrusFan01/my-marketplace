from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Notification


@login_required
def notification_list(request):
    """
    Lists the user's alerts, newest first. Opening the page marks everything
    as read, but the unread ones stay highlighted for this one view so the
    person can still see what's new.
    """
    notifications = list(Notification.objects.filter(recipient=request.user)[:100])
    unread_ids = [n.pk for n in notifications if not n.is_read]
    if unread_ids:
        Notification.objects.filter(pk__in=unread_ids).update(is_read=True)
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'unread_ids': set(unread_ids),
    })
