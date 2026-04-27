"""Celery tasks for campaign email sending."""
import uuid
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

from celery import shared_task
from django.db import models
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


def _update_progress_cache(campaign_id):
    """Cache campaign progress metrics in Redis for fast retrieval."""
    try:
        from django.core.cache import cache
        from apps.campaigns.models import Campaign
        campaign = Campaign.objects.values(
            'sent_count', 'failed_count', 'total_recipients', 'status'
        ).get(id=campaign_id)
        cache.set(f'campaign_progress_{campaign_id}', campaign, timeout=300)
    except Exception:
        pass  # Cache update is best-effort


def embed_tracking_pixel(html_body, tracking_id, base_url=None):
    """Embed a unique tracking pixel at the end of the email body."""
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    pixel_url = f"{base_url}/track/open/{tracking_id}"
    pixel_html = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;" />'
    return html_body + pixel_html


def wrap_urls_with_tracker(html_body, tracking_id, base_url=None):
    """Replace all href URLs with click tracker links."""
    import re
    if base_url is None:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    def replace_href(match):
        original_url = match.group(1)
        # Don't wrap tracking URLs or mailto links
        if original_url.startswith('/track/') or original_url.startswith('mailto:'):
            return match.group(0)
        encoded_url = quote(original_url, safe='')
        tracker_url = f"{base_url}/track/click/{tracking_id}?url={encoded_url}"
        return f'href="{tracker_url}"'

    return re.sub(r'href="([^"]+)"', replace_href, html_body)


@shared_task(bind=True, max_retries=3, queue='email_sending')
def send_email_task(self, campaign_id, recipient_id, tracking_id, personalized_content=None):
    """
    Send individual email with retry logic.
    Retries with exponential backoff: 60s, 120s, 240s.
    """
    from apps.campaigns.models import Campaign
    from apps.recipients.models import Recipient
    from apps.tracking.models import EmailLog
    from apps.smtp_config.utils import decrypt_password
    from apps.templates.serializers import render_template

    try:
        campaign = Campaign.objects.get(id=campaign_id)
        recipient = Recipient.objects.get(id=recipient_id)
        smtp_config = campaign.smtp_config

        # Get or create email log
        email_log, _ = EmailLog.objects.get_or_create(
            campaign=campaign,
            recipient=recipient,
            defaults={
                'tracking_id': uuid.UUID(tracking_id),
                'status': 'sent',
            }
        )

        # Render template content
        if personalized_content:
            html_body = personalized_content
        else:
            html_body = render_template(campaign.template.body, recipient.metadata)

        subject = render_template(campaign.subject, recipient.metadata)

        # Embed tracking pixel and wrap URLs
        html_body = embed_tracking_pixel(html_body, tracking_id)
        html_body = wrap_urls_with_tracker(html_body, tracking_id)

        # Append unsubscribe footer (legally required)
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        unsub_url = f"{base_url}/track/unsubscribe/{tracking_id}"
        html_body += (
            f'<br/><br/><hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0"/>'
            f'<p style="font-size:11px;color:#94a3b8;text-align:center">'
            f'You received this email because you are on a mailing list. '
            f'<a href="{unsub_url}" style="color:#94a3b8">Unsubscribe</a></p>'
        )

        # Build email message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = smtp_config.username
        msg['To'] = recipient.email

        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))

        # Attach file if campaign has one
        if campaign.attachment:
            import os
            from email.mime.base import MIMEBase
            from email import encoders
            try:
                attachment_path = campaign.attachment.path
                # Use the original filename from the upload, not the stored filename
                original_filename = os.path.basename(campaign.attachment.name)
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{original_filename}"')
                msg.attach(part)
            except Exception as e:
                logger.warning(f"Failed to attach file for campaign {campaign_id}: {e}")

        # Decrypt SMTP password
        password = decrypt_password(smtp_config.encrypted_password)

        # Send via SMTP
        # Port 587 uses STARTTLS (use_tls=True)
        # Port 465 uses SSL from start (use_tls=False)
        if smtp_config.port == 587 or smtp_config.use_tls:
            server = smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=30)
            server.ehlo()
            if smtp_config.use_tls:
                server.starttls()
                server.ehlo()  # required after STARTTLS
        else:
            # Port 465 or explicit SSL
            server = smtplib.SMTP_SSL(smtp_config.host, smtp_config.port, timeout=30)
            server.ehlo()

        server.login(smtp_config.username, password)
        server.sendmail(smtp_config.username, [recipient.email], msg.as_string())
        server.quit()

        # Log success
        email_log.status = 'sent'
        email_log.sent_at = timezone.now()
        email_log.save()

        # Update campaign progress atomically
        Campaign.objects.filter(id=campaign_id).update(
            sent_count=models.F('sent_count') + 1
        )
        _update_progress_cache(campaign_id)

        logger.info(f"Email sent to {recipient.email} for campaign {campaign_id}")
        return {'status': 'sent', 'recipient': recipient.email}

    except smtplib.SMTPException as exc:
        # Log failure and retry with exponential backoff
        retry_count = self.request.retries
        countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s

        try:
            from apps.tracking.models import EmailLog
            EmailLog.objects.filter(
                campaign_id=campaign_id, recipient_id=recipient_id
            ).update(
                status='failed',
                error_message=str(exc),
                retry_count=retry_count + 1,
            )
        except Exception:
            pass

        if retry_count < self.max_retries:
            logger.warning(
                f"SMTP error for {recipient_id}, retrying in {countdown}s "
                f"(attempt {retry_count + 1}/{self.max_retries}): {exc}"
            )
            raise self.retry(exc=exc, countdown=countdown)

        # Final failure
        try:
            Campaign.objects.filter(id=campaign_id).update(
                failed_count=models.F('failed_count') + 1
            )
            _update_progress_cache(campaign_id)
        except Exception:
            pass

        logger.error(f"Email permanently failed for {recipient_id}: {exc}")
        return {'status': 'failed', 'error': str(exc)}

    except Exception as exc:
        logger.error(f"Unexpected error sending email to {recipient_id}: {exc}")
        try:
            from apps.tracking.models import EmailLog
            EmailLog.objects.filter(
                campaign_id=campaign_id, recipient_id=recipient_id
            ).update(status='failed', error_message=str(exc))
            Campaign.objects.filter(id=campaign_id).update(
                failed_count=models.F('failed_count') + 1
            )
            _update_progress_cache(campaign_id)
        except Exception:
            pass
        return {'status': 'failed', 'error': str(exc)}


@shared_task(queue='email_sending')
def send_campaign(campaign_id):
    """
    Main task to orchestrate campaign sending.
    Loads campaign, personalizes content if needed, dispatches individual send tasks.
    """
    from apps.campaigns.models import Campaign
    from apps.tracking.models import EmailLog

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return

    # Update status to sending
    campaign.status = 'sending'
    campaign.started_at = timezone.now()
    campaign.save()

    # Get valid recipients
    recipients = campaign.recipient_list.recipients.filter(is_valid=True)

    # AI personalization batch (if enabled)
    personalized_map = {}
    if campaign.enable_ai_personalization:
        try:
            from apps.ai.utils import personalize_email
            for recipient in recipients:
                try:
                    personalized = personalize_email(
                        campaign.template.body, recipient.metadata
                    )
                    personalized_map[str(recipient.id)] = personalized
                except Exception as e:
                    logger.warning(f"AI personalization failed for {recipient.id}: {e}")
        except Exception as e:
            logger.warning(f"AI personalization batch failed: {e}")

    # Dispatch individual send tasks
    task_results = []
    for recipient in recipients:
        tracking_id = str(uuid.uuid4())

        # Pre-create email log
        EmailLog.objects.create(
            campaign=campaign,
            recipient=recipient,
            tracking_id=uuid.UUID(tracking_id),
            status='sent',
        )

        personalized_content = personalized_map.get(str(recipient.id))
        result = send_email_task.delay(
            str(campaign_id),
            str(recipient.id),
            tracking_id,
            personalized_content,
        )
        task_results.append(result)

    # Wait for all tasks and update final status
    # (In production, use a chord/callback instead)
    campaign.refresh_from_db()
    campaign.status = 'completed'
    campaign.completed_at = timezone.now()
    campaign.save()

    # Clear progress cache
    try:
        from django.core.cache import cache
        cache.delete(f'campaign_progress_{campaign_id}')
    except Exception:
        pass

    logger.info(f"Campaign {campaign_id} completed: {len(task_results)} emails dispatched")
    return {'status': 'completed', 'emails_dispatched': len(task_results)}
