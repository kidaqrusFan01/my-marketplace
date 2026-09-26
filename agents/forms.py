from django import forms
from .models import AgentProfile


class AgentProfileForm(forms.ModelForm):
    class Meta:
        model = AgentProfile
        fields = ['display_name', 'bio']
        widgets = {
            'display_name': forms.TextInput(attrs={'placeholder': 'e.g. your name or brand'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': "Optional — tell people what you're about"}),
        }
