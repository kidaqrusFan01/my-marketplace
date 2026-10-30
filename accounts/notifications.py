"""
Admin alerts for new registrations.

Every signup (customer or seller) emails ADMIN_NOTIFICATION_EMAIL so the
site manager finds out who just registered. Seller signups are flagged as
needing approval, with a direct link to the account in /admin/ — their
products stay hidden from shoppers until an admin approves them.

Email delivery uses the same EMAIL_* settings as the Advertise With Us
notifications (console backend by default; see corazon/settings.py for how
to switch to real SMTP).
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)


def notify_admin_new_registration(user, request=None):
    """
    Never raises: a failed email must not break someone's signup. Failures
    are logged server-side instead.
    """
    is_seller = user.is_seller
    kind = "seller" if is_seller else "customer"

    admin_path = reverse('admin:accounts_customuser_change', args=[user.pk])
    admin_url = request.build_absolute_uri(admin_path) if request else admin_path

    lines = [
        f"A new {kind} just registered on Corazon Marketplace.",
        "",
        f"Username: {user.username}",
        f"Email: {user.email}",
    ]
    if is_seller:
        lines.append(f"Store name: {user.store_name}")
    if user.phone_number:
        lines.append(f"Phone: {user.phone_number}")
    if user.referred_by:
        lines.append(f"Referred by: {user.referred_by.username}")
    lines.append(f"Registered: {user.date_joined:%d %b %Y, %H:%M} UTC")
    lines.append("")

    if is_seller:
        lines += [
            "ACTION NEEDED: this seller's products stay hidden from shoppers until you approve them.",
            f"Review & approve: {admin_url}",
            "(or tick them in the Users list and run the \"Approve selected sellers\" action)",
        ]
        subject = f"New seller registration — approval needed: {user.store_name or user.username}"
    else:
        lines.append(f"View account: {admin_url}")
        subject = f"New customer registration — {user.username}"

    try:
        send_mail(
            subject=subject,
            message="\n".join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send registration notification for user #%s", user.pk)
