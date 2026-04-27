from django.contrib import admin
from .models import RecipientList, Recipient


@admin.register(RecipientList)
class RecipientListAdmin(admin.ModelAdmin):
    """Admin interface for Recipient Lists."""
    
    list_display = ['name', 'user', 'total_count', 'valid_count', 'invalid_count', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'user__email']
    readonly_fields = ['created_at']


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """Admin interface for Recipients."""
    
    list_display = ['email', 'recipient_list', 'is_valid', 'created_at']
    list_filter = ['is_valid', 'created_at']
    search_fields = ['email', 'recipient_list__name']
    readonly_fields = ['created_at']
