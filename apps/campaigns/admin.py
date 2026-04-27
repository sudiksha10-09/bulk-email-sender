from django.contrib import admin
from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin interface for Campaigns."""
    
    list_display = ['name', 'user', 'status', 'total_recipients', 'sent_count', 'failed_count', 'created_at']
    list_filter = ['status', 'enable_ai_personalization', 'created_at']
    search_fields = ['name', 'user__email', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'subject', 'status')}),
        ('Configuration', {'fields': ('template', 'recipient_list', 'smtp_config', 'enable_ai_personalization')}),
        ('Scheduling', {'fields': ('scheduled_at', 'started_at', 'completed_at')}),
        ('Progress', {'fields': ('total_recipients', 'sent_count', 'failed_count')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
