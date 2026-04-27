import uuid
from django.db import models
from django.utils import timezone


class EmailLog(models.Model):
    """Log of individual email send attempts."""
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.CASCADE,
        related_name='email_logs'
    )
    recipient = models.ForeignKey(
        'recipients.Recipient',
        on_delete=models.CASCADE,
        related_name='email_logs'
    )
    tracking_id = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'email_logs'
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        indexes = [
            models.Index(fields=['campaign'], name='idx_emaillog_campaign'),
            models.Index(fields=['recipient'], name='idx_emaillog_recipient'),
            models.Index(fields=['tracking_id'], name='idx_emaillog_tracking'),
        ]
    
    def __str__(self):
        return f"Email to {self.recipient.email} - {self.status}"


class EmailEvent(models.Model):
    """Tracking events for email opens and clicks."""
    
    EVENT_TYPE_CHOICES = [
        ('open', 'Open'),
        ('click', 'Click'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_log = models.ForeignKey(
        EmailLog,
        on_delete=models.CASCADE,
        related_name='events'
    )
    tracking_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    event_data = models.JSONField(default=dict)  # Stores URL, user agent, IP, etc.
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'email_events'
        verbose_name = 'Email Event'
        verbose_name_plural = 'Email Events'
        indexes = [
            models.Index(fields=['email_log'], name='idx_event_emaillog'),
            models.Index(fields=['tracking_id'], name='idx_event_tracking'),
            models.Index(fields=['created_at'], name='idx_event_created'),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.tracking_id}"
