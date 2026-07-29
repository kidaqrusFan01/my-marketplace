from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from products.models import Product
from . import constants
from .forms import RedemptionRequestForm
from .models import LoyaltyAccount, LoyaltyTransaction
from .services import product_is_current_deal


@login_required
def wallet(request):
    account = LoyaltyAccount.get_or_create_for(request.user)
    transactions = account.transactions.all()[:50]
    redemption_requests = request.user.redemption_requests.all()[:20]

    if request.method == 'POST':
        form = RedemptionRequestForm(request.POST, available_balance=account.balance)
        if form.is_valid():
            redemption = form.save(commit=False)
            redemption.user = request.user
            redemption.points_used = form.cleaned_data['points_used']
            redemption.naira_value = redemption.points_used * constants.POINT_VALUE_NAIRA
            reason_map = {'airtime': 'redeemed_airtime', 'data': 'redeemed_data', 'cash': 'redeemed_cash'}
            txn = account.redeem(
                redemption.points_used, reason=reason_map[redemption.redemption_type],
                note=f"{redemption.get_redemption_type_display()} request"
            )
            if txn is None:
                messages.error(request, "That redemption couldn't be processed — your balance may have changed.")
            else:
                redemption.save()
                messages.success(
                    request,
                    f"Request submitted! {redemption.points_used} points redeemed for "
                    f"₦{redemption.naira_value:,.2f} of {redemption.get_redemption_type_display()}. "
                    "Our team will process this shortly."
                )
                return redirect('loyalty:wallet')
    else:
        form = RedemptionRequestForm(available_balance=account.balance)

    context = {
        'account': account,
        'transactions': transactions,
        'redemption_requests': redemption_requests,
        'form': form,
        'referral_url': request.build_absolute_uri('/') + f"?ref={request.user.referral_code}",
        'min_redemption_points': constants.MIN_REDEMPTION_POINTS,
        'point_value_naira': constants.POINT_VALUE_NAIRA,
    }
    return render(request, 'loyalty/wallet.html', context)


@login_required
@require_POST
def track_share(request, product_id):
    """
    Called via a small background fetch() from the Share button. Awards
    points for sharing a product's referral link — capped at once per
    user, per product, per day so spam-clicking Share can't farm points.
    Deal of the Day products earn double.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    account = LoyaltyAccount.get_or_create_for(request.user)

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    already_shared_today = LoyaltyTransaction.objects.filter(
        account=account, reason='share', related_product=product, created_at__gte=today_start
    ).exists()

    if already_shared_today:
        return JsonResponse({'awarded': False, 'balance': account.balance,
                              'message': "You've already earned points for sharing this today."})

    points = constants.SHARE_POINTS
    is_deal = product_is_current_deal(product)
    if is_deal:
        points *= constants.DEAL_OF_DAY_MULTIPLIER

    account.award(points, reason='share', related_product=product,
                  note="Deal of the Day share bonus" if is_deal else "")

    return JsonResponse({'awarded': True, 'points': points, 'balance': account.balance})
