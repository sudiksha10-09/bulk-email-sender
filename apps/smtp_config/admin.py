from django.contrib import admin
from .models import SMTPConfig


@admin.register(SMTPConfig)
class SMTPConfigAdmin(admin.ModelAdmin):
    """Admin interface for SMTP Configuration."""
    
    list_display = ['name', 'provider', 'user', 'is_validated', 'created_at']
    list_filter = ['provider', 'is_validated', 'created_at']
    search_fields = ['name', 'user__email', 'host']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'provider')}),
        ('Connection', {'fields': ('host', 'port', 'username', 'use_tls')}),
        ('Status', {'fields': ('is_validated',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
