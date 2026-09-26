from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import AgentProfileForm
from .models import AgentProfile


def agent_required(view_func):
    """
    Guards Agent-only views. Same shape as products.views.seller_required
    and for the same reason: sending an authenticated-but-not-an-agent
    user through the login page would bounce them straight back (see
    CorazonLoginView's redirect_authenticated_user) and loop forever.
    Here they're sent to the join form instead, with a clear message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        if not request.user.is_agent:
            messages.info(request, "Create your Agent profile first to access this page.")
            return redirect('agents:join')
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    """
    Public entry point at /agent/. Already an Agent? Straight to their own
    page. Logged in but haven't created a profile yet? Explain the program
    and point at the join form. Anonymous? Same explanation, pointed at
    login first.
    """
    if request.user.is_authenticated and request.user.is_agent:
        return redirect('agents:page')
    return render(request, 'agents/intro.html')


@login_required
def join(request):
    if request.user.is_agent:
        return redirect('agents:page')

    if request.method == 'POST':
        form = AgentProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            request.user.is_agent = True
            request.user.save(update_fields=['is_agent'])
            messages.success(request, "Your Agent profile is live! Start sharing products to earn Loyalty Coin.")
            return redirect('agents:page')
    else:
        form = AgentProfileForm(initial={'display_name': request.user.store_name or request.user.username})

    return render(request, 'agents/join.html', {'form': form})


@agent_required
def page(request):
    """
    An Agent's own page: who they are, their referral link, and how their
    product-sharing is performing — site-wide (any product they've
    shared, not just their own listings, since an Agent doesn't need to
    sell anything themselves).
    """
    from loyalty.models import LoyaltyAccount, LoyaltyTransaction
    from products.views import build_referral_share_url

    profile = request.user.agent_profile
    account = LoyaltyAccount.get_or_create_for(request.user)

    shares = LoyaltyTransaction.objects.filter(
        account=account, reason='share'
    ).select_related('related_product')

    total_shares = shares.count()
    total_share_bonus = shares.aggregate(total=Sum('points'))['total'] or 0

    shared_products = {}
    for txn in shares:
        if not txn.related_product:
            continue
        entry = shared_products.setdefault(txn.related_product.id, {
            'product': txn.related_product, 'share_count': 0, 'points_earned': 0,
        })
        entry['share_count'] += 1
        entry['points_earned'] += txn.points
    shared_products = sorted(shared_products.values(), key=lambda e: -e['share_count'])

    referral_bonus = account.transactions.filter(
        reason__in=['referral_purchase', 'new_buyer_bonus']
    ).aggregate(total=Sum('points'))['total'] or 0

    referral_url = build_referral_share_url(request, reverse('products:home'))

    return render(request, 'agents/page.html', {
        'profile': profile,
        'loyalty_balance': account.balance,
        'total_shares': total_shares,
        'total_share_bonus': total_share_bonus,
        'referral_bonus': referral_bonus,
        'shared_products': shared_products,
        'referral_url': referral_url,
    })
