"""URL configuration for recipients app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.recipients import views

app_name = 'recipients'

router = DefaultRouter()
router.register(r'', views.RecipientListViewSet, basename='recipient-list')

urlpatterns = [
    path('', include(router.urls)),
]
