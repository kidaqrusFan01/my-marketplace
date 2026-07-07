from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/customer/', views.CustomerSignUpView.as_view(), name='signup_customer'),
    path('signup/seller/', views.SellerSignUpView.as_view(), name='signup_seller'),
    path('login/', views.CorazonLoginView.as_view(), name='login'),
    path('logout/', views.CorazonLogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
