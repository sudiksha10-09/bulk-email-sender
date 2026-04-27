from django.contrib import admin
from .models import Template


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """Admin interface for Email Templates."""
    
    list_display = ['name', 'user', 'version', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'user__email', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('user', 'name', 'version')}),
        ('Content', {'fields': ('subject', 'body', 'variables')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
