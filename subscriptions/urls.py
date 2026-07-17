from django.urls import path

from . import views

urlpatterns = [
    path('subscriptions/', views.subscriptions_page, name='subscriptions-page'),
    path('subscriptions/plans/', views.plan_list, name='subscription-plans'),
    path('subscriptions/initiate/<int:plan_id>/', views.initiate_subscription, name='subscription-initiate'),
    path('subscriptions/webhook/momo/', views.momo_webhook, name='subscription-momo-webhook'),
    path('subscriptions/return/', views.momo_return, name='subscription-return'),
    path('subscriptions/status/', views.subscription_status, name='subscription-status'),
]
