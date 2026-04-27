"""Serializers for SMTP configuration app."""
from rest_framework import serializers
from apps.smtp_config.models import SMTPConfig


class SMTPConfigSerializer(serializers.ModelSerializer):
    """Serializer for SMTP configuration."""
    
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = SMTPConfig
        fields = (
            'id', 'name', 'provider', 'host', 'port', 
            'username', 'password', 'use_tls', 'is_validated',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_validated', 'created_at', 'updated_at')
    
    def to_representation(self, instance):
        """Don't expose encrypted password in responses."""
        data = super().to_representation(instance)
        # encrypted_password is not in fields, so it won't be exposed
        return data


class SMTPConfigCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SMTP configuration."""
    
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = SMTPConfig
        fields = (
            'name', 'provider', 'host', 'port', 
            'username', 'password', 'use_tls'
        )
    
    def validate_provider(self, value):
        """Validate provider choice."""
        valid_providers = ['gmail', 'sendgrid', 'mailgun', 'custom']
        if value not in valid_providers:
            raise serializers.ValidationError(f"Provider must be one of: {', '.join(valid_providers)}")
        return value
    
    def validate_port(self, value):
        """Validate SMTP port."""
        if value < 1 or value > 65535:
            raise serializers.ValidationError("Port must be between 1 and 65535")
        return value


class SMTPConfigUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating SMTP configuration."""
    
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = SMTPConfig
        fields = (
            'name', 'provider', 'host', 'port', 
            'username', 'password', 'use_tls'
        )
    
    def validate_port(self, value):
        """Validate SMTP port."""
        if value and (value < 1 or value > 65535):
            raise serializers.ValidationError("Port must be between 1 and 65535")
        return value
