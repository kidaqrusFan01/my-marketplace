"""
Admin/site-manager notifications for the marketing app.

Currently just email (see the EMAIL_* settings in corazon/settings.py for
how to point this at a real SMTP provider) — kept in its own module so
it's easy to add a second channel later (e.g. Slack webhook) without
touching the view logic that triggers it.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_admin_new_inquiry(inquiry):
    """
    Emails ADMIN_NOTIFICATION_EMAIL whenever a BusinessInquiry is
    submitted on /advertise/, so a real person finds out immediately
    instead of only via checking the Django admin later.

    Never raises — a failed notification (e.g. real SMTP not configured
    yet) should never break the inquiry submission itself for the person
    filling out the form. Failures are logged server-side instead.
    """
    plan_line = f"\nInterested plan: {inquiry.interested_plan_display}" if inquiry.interested_plan else ""
    phone_line = f"\nPhone: {inquiry.phone_number}" if inquiry.phone_number else ""

    subject = f"New {inquiry.get_inquiry_type_display()} inquiry — {inquiry.company_name}"
    body = (
        f"A new inquiry was submitted on the Advertise With Us page.\n\n"
        f"Type: {inquiry.get_inquiry_type_display()}{plan_line}\n"
        f"Company: {inquiry.company_name}\n"
        f"Contact: {inquiry.contact_name}\n"
        f"Email: {inquiry.email}{phone_line}\n\n"
        f"Message:\n{inquiry.message or '(no message provided)'}\n\n"
        f"Review it at: /admin/marketing/businessinquiry/{inquiry.pk}/change/"
    )

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send inquiry notification email for inquiry #%s", inquiry.pk)
