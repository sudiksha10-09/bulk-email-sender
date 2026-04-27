import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Template(models.Model):
    """Email template with personalization variables."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    variables = models.JSONField(default=list)  # List of variable definitions
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'templates'
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        indexes = [
            models.Index(fields=['user'], name='idx_template_user'),
        ]
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
