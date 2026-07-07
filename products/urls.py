from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/product/add/', views.product_create, name='product_create'),
    path('seller/product/<int:pk>/edit/', views.product_update, name='product_update'),
    path('seller/product/<int:pk>/delete/', views.product_delete, name='product_delete'),
]
