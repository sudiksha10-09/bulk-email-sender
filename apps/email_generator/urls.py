"""
Email Generator URL config — standalone module.
Remove these 2 lines from config/urls.py to disable:
  from apps.email_generator import urls as generator_urls  (auto-imported)
  path('generator/', include('apps.email_generator.urls')),
"""
from django.urls import path
from apps.email_generator import views

urlpatterns = [
    path('', views.generator_page, name='generator'),
    path('api/generate', views.generate_emails, name='generator_generate'),
    path('api/export', views.export_csv, name='generator_export'),
]
