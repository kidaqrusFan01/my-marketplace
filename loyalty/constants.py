"""
Corazon Marketplace loyalty coin — economy constants.

Keeping every number in one file makes it easy to tune the point economy
later without hunting through views. All amounts are in *points*, except
POINT_VALUE_NAIRA which is the conversion rate used for redemptions.
"""
from decimal import Decimal

# --- Earning ---
# Buying: ~1% of what you spend, back as points (1 point per ₦100 spent).
POINTS_PER_100_NAIRA_SPENT = 1

# Sharing a product's referral link (awarded once per user, per product,
# per calendar day — prevents spam-clicking the Share button for points).
SHARE_POINTS = 20

# Someone used your referral link and completed a purchase.
REFERRAL_PURCHASE_POINTS = 200

# Extra bonus on top of the above if that buyer had never ordered before
# (i.e. your referral brought in a genuinely new customer).
NEW_BUYER_BONUS_POINTS = 300

# Deal of the Day: sharing or buying the featured deal earns extra —
# this multiplies SHARE_POINTS / REFERRAL_PURCHASE_POINTS / NEW_BUYER_BONUS_POINTS,
# and adds a flat bonus on top of ordinary purchase points.
DEAL_OF_DAY_MULTIPLIER = 2
DEAL_OF_DAY_PURCHASE_BONUS = 100

# --- Redemption ---
# 1 point = ₦1 when redeemed for a discount, delivery fee, or converted
# to airtime/data/cash.
POINT_VALUE_NAIRA = Decimal('1.00')

# Minimum points required to submit an airtime/data/cash redemption request
# (keeps tiny/spammy redemption requests from cluttering fulfillment).
MIN_REDEMPTION_POINTS = 100
