from django import forms
from .models import JobApplication


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['full_name', 'email', 'phone_number', 'resume', 'cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Tell us why you would be a great fit...'}),
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            valid_extensions = ('.pdf', '.doc', '.docx')
            if not resume.name.lower().endswith(valid_extensions):
                raise forms.ValidationError("Please upload a PDF or Word document.")
            if resume.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Resume file must be smaller than 5MB.")
        return resume
