from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_seller', 'is_staff', 'is_active')
    list_filter = ('is_seller', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Marketplace Info', {'fields': ('is_seller', 'phone_number', 'address', 'store_name')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Marketplace Info', {'fields': ('is_seller', 'email', 'store_name')}),
    )
