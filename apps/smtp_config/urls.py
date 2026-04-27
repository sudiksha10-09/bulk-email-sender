"""URL configuration for SMTP configuration app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.smtp_config import views

app_name = 'smtp_config'

router = DefaultRouter()
router.register(r'', views.SMTPConfigViewSet, basename='smtp-config')

urlpatterns = [
    path('', include(router.urls)),
]
