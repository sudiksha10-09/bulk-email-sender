from django.urls import path
from apps.billing import views

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('cancel/', views.cancel_subscription, name='cancel'),
]
