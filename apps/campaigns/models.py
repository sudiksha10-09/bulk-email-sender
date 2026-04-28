import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


def campaign_attachment_path(instance, filename):
    """Generate upload path preserving original filename."""
    # Store original filename in a way that preserves it
    # Format: attachments/campaign_uuid/original_filename.ext
    return f'attachments/{instance.id}/{filename}'


class Campaign(models.Model):
    """Email campaign configuration and tracking."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='campaigns',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    template = models.ForeignKey(
        'templates.Template',
        on_delete=models.PROTECT,
        related_name='campaigns'
    )
    recipient_list = models.ForeignKey(
        'recipients.RecipientList',
        on_delete=models.PROTECT,
        related_name='campaigns'
    )
    smtp_config = models.ForeignKey(
        'smtp_config.SMTPConfig',
        on_delete=models.PROTECT,
        related_name='campaigns'
    )
    enable_ai_personalization = models.BooleanField(default=False)
    attachment = models.FileField(upload_to=campaign_attachment_path, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaigns'
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        indexes = [
            models.Index(fields=['user'], name='idx_campaign_user'),
            models.Index(fields=['status'], name='idx_campaign_status'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.status})"
