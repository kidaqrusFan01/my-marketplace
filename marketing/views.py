from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .forms import BusinessInquiryForm, VendorPlanRequestForm

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


def pricing(request):
    """
    Public pricing page — anyone can view it, but only logged-in sellers
    can actually request a plan (they need a seller account to have
    products to list in the first place). Non-sellers see a "Become a
    Seller" prompt on each paid tier's button instead of a request form.
    """
    from .constants import VENDOR_PLANS, BANK_TRANSFER_DETAILS, WHATSAPP_NUMBER
    from .models import VendorSubscription, VendorPlanRequest

    current_plan = 'free'
    pending_request = None
    if request.user.is_authenticated and request.user.is_seller:
        subscription = VendorSubscription.objects.filter(seller=request.user).first()
        current_plan = subscription.current_plan if subscription else 'free'
        pending_request = VendorPlanRequest.objects.filter(
            seller=request.user, status='pending'
        ).first()

    if request.method == 'POST' and request.user.is_authenticated and request.user.is_seller:
        requested_plan = request.POST.get('plan')
        valid_keys = [p['key'] for p in VENDOR_PLANS]
        if requested_plan not in valid_keys:
            messages.error(request, "That's not a valid plan.")
            return redirect('marketing:pricing')

        if requested_plan == 'free':
            # No payment needed — just set it directly.
            subscription = VendorSubscription.get_or_create_for(request.user)
            subscription.current_plan = 'free'
            subscription.save(update_fields=['current_plan'])
            messages.success(request, "You're on the Free plan.")
            return redirect('marketing:pricing')

        form = VendorPlanRequestForm(request.POST)
        if form.is_valid():
            plan_request = form.save(commit=False)
            plan_request.seller = request.user
            plan_request.requested_plan = requested_plan
            plan_request.save()
            messages.success(
                request,
                f"Request received for the {requested_plan.title()} plan! Complete the bank "
                "transfer below, then send proof of payment on WhatsApp — we'll activate your "
                "plan as soon as it's confirmed."
            )
            return redirect('marketing:pricing')

    return render(request, 'marketing/pricing.html', {
        'plans': VENDOR_PLANS,
        'current_plan': current_plan,
        'pending_request': pending_request,
        'bank_details': BANK_TRANSFER_DETAILS,
        'whatsapp_number': WHATSAPP_NUMBER,
        'note_form': VendorPlanRequestForm(),
    })
