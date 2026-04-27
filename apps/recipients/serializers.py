"""Serializers for recipients app."""
from rest_framework import serializers
from apps.recipients.models import RecipientList, Recipient


class RecipientSerializer(serializers.ModelSerializer):
    """Serializer for individual recipients."""
    
    class Meta:
        model = Recipient
        fields = ('id', 'email', 'metadata', 'is_valid', 'validation_error', 'created_at')
        read_only_fields = ('id', 'created_at')


class RecipientListSerializer(serializers.ModelSerializer):
    """Serializer for recipient lists."""
    
    recipients = RecipientSerializer(many=True, read_only=True)
    
    class Meta:
        model = RecipientList
        fields = (
            'id', 'name', 'total_count', 'valid_count', 'invalid_count',
            'csv_file_url', 'status', 'created_at', 'recipients'
        )
        read_only_fields = (
            'id', 'total_count', 'valid_count', 'invalid_count',
            'csv_file_url', 'status', 'created_at'
        )


class RecipientListCreateSerializer(serializers.Serializer):
    """Serializer for creating recipient list with CSV upload."""
    
    name = serializers.CharField(max_length=255, required=True)
    csv_file = serializers.FileField(required=True)
    
    def validate_csv_file(self, value):
        """Validate CSV file size and type."""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f"CSV file too large. Maximum size is 10MB. Your file is {value.size / (1024 * 1024):.2f}MB"
            )
        
        # Check file extension
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV file (.csv extension)")
        
        return value
