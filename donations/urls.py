from django.urls import path

from . import views

urlpatterns = [
    path('donations/to/<str:username>/', views.initiate_donation, name='donation-initiate'),
    path('donations/webhook/momo/', views.momo_donation_webhook, name='donation-momo-webhook'),
    path('donations/return/', views.momo_donation_return, name='donation-return'),
    path('donations/summary/<str:username>/', views.creator_donation_summary, name='donation-summary'),
]
