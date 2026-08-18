from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('returns/', views.return_policy, name='returns'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('advertise/', views.advertise_with_us, name='advertise'),
    path('pricing/', views.pricing, name='pricing'),
    path('recent-activity/', views.recent_activity, name='recent_activity'),
]
