import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class SMTPConfig(models.Model):
    """SMTP configuration for sending emails."""
    
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('custom', 'Custom SMTP'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='smtp_configs'
    )
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    encrypted_password = models.BinaryField()  # Stores encrypted password
    use_tls = models.BooleanField(default=True)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'smtp_configs'
        verbose_name = 'SMTP Configuration'
        verbose_name_plural = 'SMTP Configurations'
        indexes = [
            models.Index(fields=['user'], name='idx_smtp_user'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
