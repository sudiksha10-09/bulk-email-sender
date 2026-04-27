"""URL configuration for AI service."""
from django.urls import path
from apps.ai import views

app_name = 'ai'

urlpatterns = [
    path('generate-subjects', views.generate_subjects, name='generate-subjects'),
    path('spam-check', views.spam_check, name='spam-check'),
    path('personalize', views.personalize, name='personalize'),
]
