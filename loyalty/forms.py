from django import forms

from . import constants
from .models import RedemptionRequest


class RedemptionRequestForm(forms.ModelForm):
    class Meta:
        model = RedemptionRequest
        fields = ['redemption_type', 'points_used', 'phone_number', 'bank_details']
        widgets = {
            'points_used': forms.NumberInput(attrs={'min': constants.MIN_REDEMPTION_POINTS, 'step': 1}),
            'phone_number': forms.TextInput(attrs={'placeholder': '080XXXXXXXX'}),
            'bank_details': forms.TextInput(attrs={'placeholder': 'Bank name, account number, account name'}),
        }

    def __init__(self, *args, available_balance=0, **kwargs):
        self.available_balance = available_balance
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        points = cleaned.get('points_used')
        rtype = cleaned.get('redemption_type')

        if points is not None:
            if points < constants.MIN_REDEMPTION_POINTS:
                self.add_error('points_used', f"You need at least {constants.MIN_REDEMPTION_POINTS} points to redeem.")
            elif points > self.available_balance:
                self.add_error('points_used', f"You only have {self.available_balance} points available.")

        if rtype in ('airtime', 'data') and not cleaned.get('phone_number'):
            self.add_error('phone_number', "Phone number is required for airtime/data redemptions.")
        if rtype == 'cash' and not cleaned.get('bank_details'):
            self.add_error('bank_details', "Bank account details are required for cash payouts.")

        return cleaned
