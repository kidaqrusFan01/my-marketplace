from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    points_to_redeem = forms.IntegerField(
        required=False, min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'min': 0, 'step': 1}),
        help_text="Optional — apply your loyalty points as a discount on this order."
    )

    class Meta:
        model = Order
        fields = ['full_name', 'email', 'address', 'city', 'postal_code', 'phone_number']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email address'}),
            'address': forms.TextInput(attrs={'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal code'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone number'}),
        }

    def __init__(self, *args, available_points=0, order_subtotal=0, **kwargs):
        self.available_points = available_points
        self.order_subtotal = order_subtotal
        super().__init__(*args, **kwargs)
        if available_points:
            self.fields['points_to_redeem'].help_text = (
                f"You have {available_points} points available "
                f"(₦{available_points:,} max discount)."
            )

    def clean_points_to_redeem(self):
        points = self.cleaned_data.get('points_to_redeem') or 0
        if points > self.available_points:
            raise forms.ValidationError(f"You only have {self.available_points} points available.")
        # 1 point = ₦1 — don't let someone "redeem" more points than the
        # order is even worth; cap it down instead of erroring, since this
        # is just wasted value for them, not something we need to block.
        if self.order_subtotal and points > self.order_subtotal:
            points = int(self.order_subtotal)
        return points
