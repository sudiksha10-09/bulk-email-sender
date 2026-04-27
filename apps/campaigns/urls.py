"""URL configuration for campaigns app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.campaigns import views

app_name = 'campaigns'

router = DefaultRouter()
router.register(r'', views.CampaignViewSet, basename='campaign')

urlpatterns = [
    path('', include(router.urls)),
]
