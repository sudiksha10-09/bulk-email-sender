"""URL configuration for bulk email sender project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, Http404
from pathlib import Path


def frontend_view(request):
    html = (Path(settings.BASE_DIR) / 'frontend' / 'index.html').read_text(encoding='utf-8')
    return HttpResponse(html)


def app_view(request):
    html = (Path(settings.BASE_DIR) / 'frontend' / 'app.html').read_text(encoding='utf-8')
    return HttpResponse(html)


def landing_view(request):
    html = (Path(settings.BASE_DIR) / 'frontend' / 'landing.html').read_text(encoding='utf-8')
    return HttpResponse(html)


def pricing_view(request):
    html = (Path(settings.BASE_DIR) / 'frontend' / 'pricing.html').read_text(encoding='utf-8')
    return HttpResponse(html)


urlpatterns = [
    path('', landing_view, name='landing'),
    path('app/', app_view, name='app'),
    path('app.html', app_view, name='app_html'),
    path('landing.html', landing_view, name='landing_html'),
    path('pricing.html', pricing_view, name='pricing_html'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/smtp-configs/', include('apps.smtp_config.urls')),
    path('api/recipient-lists/', include('apps.recipients.urls')),
    path('api/templates/', include('apps.templates.urls')),
    path('api/campaigns/', include('apps.campaigns.urls')),
    path('api/ai/', include('apps.ai.urls')),
    path('api/billing/', include('apps.billing.urls')),
    path('api/webhooks/', include('apps.tracking.webhook_urls')),
    path('track/', include('apps.tracking.urls')),
    # ── COLD EMAIL GENERATOR (standalone — remove these 2 lines to disable) ──
    path('generator/', include('apps.email_generator.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
