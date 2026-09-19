"""
Vendor listing plans shown on the /pricing/ page.

Pricing and feature copy lives here in one place (not scattered across
templates) so it's easy to update later. All amounts are monthly, in Naira.

>>> HOW TO ACTIVATE PAYMENTS FOR REAL <<<
This project does not process payments automatically — per the brief, all
plans are paid by bank transfer and confirmed manually over WhatsApp. Two
placeholders below need real values before this goes live:
  1. BANK_TRANSFER_DETAILS — your real account name/number/bank.
  2. WHATSAPP_NUMBER — the WhatsApp number to receive payment confirmations.
Both are also called out in templates/marketing/pricing.html.
"""

BANK_TRANSFER_DETAILS = {
    'account_name': "REPLACE WITH ACCOUNT NAME",
    'account_number': "REPLACE WITH ACCOUNT NUMBER",
    'bank_name': "REPLACE WITH BANK NAME",
}

# TODO: replace with the real WhatsApp number, digits only with country code,
# e.g. "2348012345678" for a Nigerian number starting 0801... — used to build
# a wa.me click-to-chat link on the pricing page.
WHATSAPP_NUMBER = "234XXXXXXXXXX"

VENDOR_PLANS = [
    {
        'key': 'free',
        'name': 'Free',
        'subtitle': 'Starter',
        'price': 0,
        'is_recommended': False,
        'features': [
            'List your products on the marketplace',
            'Standard seller dashboard access',
            'Appears in category & search listings',
        ],
    },
    {
        'key': 'growth',
        'name': 'Growth',
        'subtitle': 'For sellers ready to grow',
        'price': 5000,
        'is_recommended': False,
        'features': [
            'Everything in Free',
            'Priority placement within your category',
            'Boosted visibility in search results',
        ],
    },
    {
        'key': 'business',
        'name': 'Business',
        'subtitle': 'Serious sellers',
        'price': 10000,
        'is_recommended': True,
        'features': [
            'Everything in Growth',
            'Featured on the homepage first page',
            'Priority support from our team',
        ],
    },
    {
        'key': 'premium',
        'name': 'Premium',
        'subtitle': 'Maximum visibility',
        'price': 15000,
        'is_recommended': False,
        'features': [
            'Everything in Business',
            'Eligible for Deal of the Day placement',
            'The best possible product listing on the site',
        ],
    },
]

VENDOR_PLAN_KEYS = [plan['key'] for plan in VENDOR_PLANS]


def get_plan(key):
    return next((p for p in VENDOR_PLANS if p['key'] == key), None)


# ----------------------------------------------------------------------
# Advertising plans — shown on /advertise/ (banner ads + job postings for
# businesses, as opposed to VENDOR_PLANS above which is about a seller's
# own product-listing placement). Structure/price points follow the
# reference pricing design supplied for this page: 4 tiers, monthly or
# yearly billing (20% off yearly), with higher tiers unlocking more
# banner ad inventory and job-posting volume.
# ----------------------------------------------------------------------
ADVERTISING_YEARLY_DISCOUNT_PERCENT = 20

ADVERTISING_PLANS = [
    {
        'key': 'starter',
        'name': 'Starter',
        'subtitle': 'For testing the waters',
        'price': 0,
        'badge': None,
        'cta_text': 'Start Free',
        'features': [
            'Submit unlimited inquiries to our team',
            '1 job posting per month on the Careers page',
            'Listed in our advertiser directory',
        ],
    },
    {
        'key': 'growth',
        'name': 'Growth',
        'subtitle': 'Most businesses start here',
        'price': 10000,
        'badge': 'Most Popular',
        'cta_text': 'Choose Growth',
        'features': [
            'Everything in Starter',
            '1 homepage banner slot (7 days/month)',
            '5 job postings per month',
            'Standard placement in the ad rotation',
        ],
    },
    {
        'key': 'business',
        'name': 'Business',
        'subtitle': 'For serious brands',
        'price': 25000,
        'badge': None,
        'cta_text': 'Go Business',
        'features': [
            'Everything in Growth',
            '2 homepage banner slots, ongoing',
            '20 job postings per month',
            'Priority placement in the ad rotation',
        ],
    },
    {
        'key': 'enterprise',
        'name': 'Enterprise',
        'subtitle': 'Best for big brands',
        'price': 50000,
        'badge': 'Best for Big Brands',
        'cta_text': 'Contact Sales',
        'features': [
            'Everything in Business',
            'Dedicated homepage banner slot',
            'Unlimited job postings',
            'Dedicated account manager',
        ],
    },
]

ADVERTISING_PLAN_KEYS = [plan['key'] for plan in ADVERTISING_PLANS]

# Precompute each plan's discounted yearly total once, here, rather than
# doing price math inside the template (which Django's template language
# is deliberately bad at — {% widthratio %} works but is fragile/unclear).
for _plan in ADVERTISING_PLANS:
    _plan['price_yearly'] = round(_plan['price'] * 12 * (1 - ADVERTISING_YEARLY_DISCOUNT_PERCENT / 100))
del _plan


def get_advertising_plan(key):
    return next((p for p in ADVERTISING_PLANS if p['key'] == key), None)
