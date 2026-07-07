from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<slug:slug>/', views.job_detail, name='job_detail'),
]
