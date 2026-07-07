from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
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
