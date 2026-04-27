import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class RecipientList(models.Model):
    """A collection of email recipients uploaded via CSV."""
    
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipient_lists'
    )
    name = models.CharField(max_length=255)
    total_count = models.IntegerField(default=0)
    valid_count = models.IntegerField(default=0)
    invalid_count = models.IntegerField(default=0)
    csv_file_url = models.URLField(max_length=500)  # S3 URL
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'recipient_lists'
        verbose_name = 'Recipient List'
        verbose_name_plural = 'Recipient Lists'
        indexes = [
            models.Index(fields=['user'], name='idx_reciplist_user'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.valid_count} recipients)"


class Recipient(models.Model):
    """Individual email recipient with metadata."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient_list = models.ForeignKey(
        RecipientList,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    email = models.EmailField(max_length=255)
    metadata = models.JSONField(default=dict)  # Stores name, company, custom fields
    is_valid = models.BooleanField(default=True)
    validation_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'recipients'
        verbose_name = 'Recipient'
        verbose_name_plural = 'Recipients'
        indexes = [
            models.Index(fields=['recipient_list'], name='idx_recip_list'),
            models.Index(fields=['email'], name='idx_recip_email'),
        ]
    
    def __str__(self):
        return self.email
