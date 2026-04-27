"""Views for email tracking and analytics."""
import base64
import logging
from urllib.parse import unquote

from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.tracking.models import EmailLog, EmailEvent

logger = logging.getLogger(__name__)

# 1x1 transparent PNG pixel (base64 encoded)
TRACKING_PIXEL_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
TRACKING_PIXEL = base64.b64decode(TRACKING_PIXEL_B64)


@csrf_exempt
def track_open(request, tracking_id):
    """
    GET /track/open/{tracking_id}
    Record email open event and return 1x1 transparent PNG.
    """
    try:
        email_log = EmailLog.objects.get(tracking_id=tracking_id)
        EmailEvent.objects.create(
            email_log=email_log,
            tracking_id=email_log.tracking_id,
            event_type='open',
            event_data={
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': _get_client_ip(request),
                'timestamp': timezone.now().isoformat(),
            }
        )
    except EmailLog.DoesNotExist:
        pass  # Silently ignore unknown tracking IDs
    except Exception as e:
        logger.error(f"Error recording open event for {tracking_id}: {e}")

    return HttpResponse(
        TRACKING_PIXEL,
        content_type='image/png',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        }
    )


@csrf_exempt
def track_click(request, tracking_id):
    """
    GET /track/click/{tracking_id}?url={encoded_url}
    Record click event and redirect to original URL.
    """
    original_url = request.GET.get('url', '')

    if not original_url:
        return HttpResponse('Missing URL parameter', status=400)

    # Decode URL
    try:
        decoded_url = unquote(original_url)
    except Exception:
        decoded_url = original_url

    try:
        email_log = EmailLog.objects.get(tracking_id=tracking_id)
        EmailEvent.objects.create(
            email_log=email_log,
            tracking_id=email_log.tracking_id,
            event_type='click',
            event_data={
                'url': decoded_url,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': _get_client_ip(request),
                'timestamp': timezone.now().isoformat(),
            }
        )
    except EmailLog.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Error recording click event for {tracking_id}: {e}")

    return HttpResponseRedirect(decoded_url)


@api_view(['POST'])
@permission_classes([AllowAny])
def bounce_webhook(request):
    """
    POST /api/webhooks/bounce
    Handle bounce notifications from SMTP providers.
    """
    email = request.data.get('email', '').lower()
    bounce_type = request.data.get('bounce_type', 'hard')
    reason = request.data.get('reason', 'Unknown bounce reason')

    if not email:
        return Response({'error': 'email is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Update all recent email logs for this email to bounced
    updated = EmailLog.objects.filter(
        recipient__email=email,
        status='sent',
    ).update(
        status='bounced',
        error_message=f"{bounce_type}: {reason}",
    )

    logger.info(f"Bounce recorded for {email}: {reason} ({updated} logs updated)")
    return Response({'success': True, 'updated': updated})


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@csrf_exempt
def unsubscribe(request, tracking_id):
    """
    GET /track/unsubscribe/{tracking_id}
    Mark recipient as unsubscribed and show confirmation page.
    """
    try:
        email_log = EmailLog.objects.select_related('recipient').get(tracking_id=tracking_id)
        recipient = email_log.recipient
        # Mark as invalid so they won't receive future emails
        recipient.is_valid = False
        recipient.validation_error = 'Unsubscribed'
        recipient.save()
        email = recipient.email
    except EmailLog.DoesNotExist:
        email = 'your address'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/>
<style>body{{font-family:sans-serif;background:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.box{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:40px;max-width:420px;text-align:center}}
h2{{color:#1e293b;margin-bottom:10px}}p{{color:#64748b;font-size:14px;line-height:1.6}}
.check{{font-size:48px;margin-bottom:16px}}</style></head>
<body><div class="box">
<div class="check">✅</div>
<h2>Unsubscribed</h2>
<p><strong>{email}</strong> has been removed from this mailing list.<br/>You won't receive further emails from this campaign.</p>
</div></body></html>"""
    return HttpResponse(html)
