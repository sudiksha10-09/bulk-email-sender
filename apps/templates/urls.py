"""URL configuration for templates app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.templates import views

app_name = 'templates'

router = DefaultRouter()
router.register(r'', views.TemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
]
