"""URL configuration for tracking app."""
from django.urls import path
from apps.tracking import views

app_name = 'tracking'

urlpatterns = [
    path('open/<uuid:tracking_id>', views.track_open, name='track-open'),
    path('click/<uuid:tracking_id>', views.track_click, name='track-click'),
    path('unsubscribe/<uuid:tracking_id>', views.unsubscribe, name='unsubscribe'),
]
