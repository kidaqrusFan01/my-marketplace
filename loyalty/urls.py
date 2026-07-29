from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    path('wallet/', views.wallet, name='wallet'),
    path('track-share/<int:product_id>/', views.track_share, name='track_share'),
]
