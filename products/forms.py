from django import forms
from .models import Product, Category, Review


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'discount_price', 'stock', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        # Only validate if a NEW file was uploaded this submission (editing
        # a product without touching the image passes an unchanged FieldFile,
        # which has no content_type attribute).
        if image and hasattr(image, 'content_type'):
            valid_types = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
            if image.content_type not in valid_types:
                raise forms.ValidationError("Please upload a JPEG, PNG, WEBP, or GIF image.")
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Image file must be smaller than 10MB.")
        return image


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} star{'s' if i != 1 else ''}") for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your thoughts on this product...'}),
        }
