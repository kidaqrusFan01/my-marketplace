from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .forms import BusinessInquiryForm

# Shown when there isn't enough real order activity yet to fill the toast
# feed (e.g. a freshly-seeded install) — keeps the "site feels alive"
# effect honest (never fabricates a fake purchase) while still having
# something friendly to show.
FALLBACK_ACTIVITY_MESSAGES = [
    "🪙 Earn loyalty points on every purchase you make here.",
    "🔥 Check out today's Deal of the Day for bonus points.",
    "📦 Fast delivery across Nigeria on thousands of products.",
    "🎁 Share a product with friends to earn referral rewards.",
    "⭐ New sellers join Corazon Marketplace every week.",
]


def recent_activity(request):
    """
    Polled by the small "live activity" ticker in the corner of the site
    (see script.js). Returns real, recent, anonymized purchase activity —
    product name + buyer's city + how long ago, no names/emails — so the
    "feels alive" effect is honest rather than manufactured social proof.
    Falls back to friendly rotating tips if there's no order history yet.
    """
    from django.utils import timezone
    from orders.models import OrderItem

    items = list(
        OrderItem.objects.select_related('order', 'product')
        .exclude(product__isnull=True)
        .order_by('-order__created_at')[:15]
    )

    events = []
    now = timezone.now()
    for item in items:
        if not item.order.created_at:
            continue
        seconds_ago = max(int((now - item.order.created_at).total_seconds()), 60)
        minutes_ago = seconds_ago // 60
        if minutes_ago < 60:
            when = f"{minutes_ago} min ago" if minutes_ago >= 1 else "just now"
        else:
            when = f"{minutes_ago // 60}h ago"
        city = item.order.city or "Nigeria"
        events.append(f"🛒 Someone in {city} just bought {item.product_name} · {when}")

    if not events:
        events = FALLBACK_ACTIVITY_MESSAGES

    return JsonResponse({'events': events})


def about(request):
    return render(request, 'marketing/about.html')


def return_policy(request):
    return render(request, 'marketing/return_policy.html')


def terms_and_conditions(request):
    return render(request, 'marketing/terms.html')


def advertise_with_us(request):
    # Supports being linked to with a preselected inquiry type, e.g. the
    # "we advertise jobs here" banner on the careers page links here with
    # ?type=job_posting so the form opens with the right option chosen.
    from .models import BusinessInquiry
    initial_type = request.GET.get('type', 'advertising')
    if initial_type not in dict(BusinessInquiry.INQUIRY_TYPE_CHOICES):
        initial_type = 'advertising'

    if request.method == 'POST':
        form = BusinessInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thanks! Your inquiry was received — our team will reach out to you by email shortly."
            )
            return redirect('marketing:advertise')
    else:
        form = BusinessInquiryForm(initial={'inquiry_type': initial_type})

    return render(request, 'marketing/advertise.html', {'form': form})
