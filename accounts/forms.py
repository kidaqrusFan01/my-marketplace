from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_seller = False
        if commit:
            user.save()
        return user


class SellerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    store_name = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'store_name', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.store_name = self.cleaned_data['store_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.is_seller = True
        # Sellers get limited staff access so they can log into /admin/ and
        # manage ONLY their own products (scoped via ProductAdmin.get_queryset).
        user.is_staff = True
        if commit:
            user.save()
            self._grant_seller_permissions(user)
        return user

    @staticmethod
    def _grant_seller_permissions(user):
        from django.contrib.auth.models import Permission
        from products.models import Product, ProductImage

        codenames = [
            'add_product', 'change_product', 'view_product', 'delete_product',
            'add_productimage', 'change_productimage', 'view_productimage', 'delete_productimage',
        ]
        perms = Permission.objects.filter(codename__in=codenames)
        user.user_permissions.set(perms)


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'store_name')
