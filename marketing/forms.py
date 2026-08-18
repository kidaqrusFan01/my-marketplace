from django import forms
from .models import BusinessInquiry, VendorPlanRequest


class BusinessInquiryForm(forms.ModelForm):
    class Meta:
        model = BusinessInquiry
        fields = ['inquiry_type', 'company_name', 'contact_name', 'email', 'phone_number', 'message']
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'Your company or brand name'}),
            'contact_name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@company.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '080XXXXXXXX (optional)'}),
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us a bit about what you have in mind...'}),
        }


class VendorPlanRequestForm(forms.ModelForm):
    class Meta:
        model = VendorPlanRequest
        fields = ['note']
        widgets = {
            'note': forms.TextInput(attrs={'placeholder': "Optional — e.g. \"I'll transfer this evening\""}),
        }
