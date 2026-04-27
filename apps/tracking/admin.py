from django.contrib import admin
from .models import EmailLog, EmailEvent


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Admin interface for Email Logs."""
    
    list_display = ['tracking_id', 'campaign', 'recipient', 'status', 'retry_count', 'sent_at']
    list_filter = ['status', 'created_at']
    search_fields = ['tracking_id', 'recipient__email', 'campaign__name']
    readonly_fields = ['created_at']


@admin.register(EmailEvent)
class EmailEventAdmin(admin.ModelAdmin):
    """Admin interface for Email Events."""
    
    list_display = ['tracking_id', 'event_type', 'email_log', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['tracking_id', 'email_log__recipient__email']
    readonly_fields = ['created_at']
