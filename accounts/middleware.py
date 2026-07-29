from django.utils.deprecation import MiddlewareMixin


class ReferralTrackingMiddleware(MiddlewareMixin):
    """
    Catches ?ref=<code> on ANY page (a shared product link, the homepage,
    anywhere) and remembers it in the session, so that whichever signup
    page the visitor eventually lands on can credit the right referrer.

    This is deliberately "last touch": if someone clicks two different
    referral links before signing up, the most recent one wins. We only
    store the code itself here — actually crediting a referral happens
    once, at signup (accounts.views), by copying this into the new user's
    `referred_by` field.
    """

    def process_request(self, request):
        ref_code = request.GET.get('ref')
        if ref_code:
            # Keep it short and clean — referral_code is always uppercase
            # hex from CustomUser._generate_unique_referral_code().
            request.session['referral_code'] = ref_code.strip().upper()[:12]
        return None
