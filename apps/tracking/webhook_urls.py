"""Webhook URL configuration for tracking app."""
from django.urls import path
from apps.tracking import views

urlpatterns = [
    path('bounce', views.bounce_webhook, name='bounce-webhook'),
]
