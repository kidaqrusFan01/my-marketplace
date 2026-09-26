from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('page/', views.page, name='page'),
]
