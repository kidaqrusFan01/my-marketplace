from django import forms

QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]


class CartAddProductForm(forms.Form):
    quantity = forms.TypedChoiceField(
        choices=QUANTITY_CHOICES, coerce=int, initial=1,
        widget=forms.Select(attrs={'class': 'qty-select'})
    )
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
