"""
Currency formatting for Corazon Marketplace.

The site displays all prices in Nigerian Naira by default. Rather than
hardcoding a currency symbol in every template, prices are run through
this filter so formatting (symbol, thousands separators, decimal places)
stays consistent everywhere and can be changed in one place later if the
site ever needs to support multiple currencies.
"""
from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()


@register.filter(name='naira')
def naira(value):
    """
    Formats a number as Nigerian Naira, e.g.:
        49999      -> '₦49,999.00'
        1250000.5  -> '₦1,250,000.50'
        None       -> '₦0.00'
    """
    if value in (None, ''):
        value = 0
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value
    return f"₦{amount:,.2f}"
