"""Serializers for campaigns app."""
from rest_framework import serializers
from apps.campaigns.models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    """Full campaign serializer."""

    class Meta:
        model = Campaign
        fields = (
            'id', 'name', 'subject', 'template', 'recipient_list', 'smtp_config',
            'enable_ai_personalization', 'status', 'scheduled_at',
            'started_at', 'completed_at', 'total_recipients',
            'sent_count', 'failed_count', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'status', 'started_at', 'completed_at',
            'total_recipients', 'sent_count', 'failed_count',
            'created_at', 'updated_at',
        )


class CampaignListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing campaigns."""

    class Meta:
        model = Campaign
        fields = (
            'id', 'name', 'status', 'total_recipients',
            'sent_count', 'failed_count', 'created_at',
        )
        read_only_fields = fields


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating campaigns."""

    class Meta:
        model = Campaign
        fields = (
            'name', 'subject', 'template', 'recipient_list',
            'smtp_config', 'enable_ai_personalization', 'scheduled_at', 'attachment',
        )
        extra_kwargs = {
            'scheduled_at': {'required': False},
            'enable_ai_personalization': {'required': False},
            'attachment': {'required': False},
        }

    def validate_template(self, value):
        # No user validation needed since auth is removed
        return value

    def validate_recipient_list(self, value):
        # No user validation needed since auth is removed
        return value

    def validate_smtp_config(self, value):
        # No user validation needed since auth is removed
        return value


class CampaignUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating draft campaigns."""

    class Meta:
        model = Campaign
        fields = (
            'name', 'subject', 'template', 'recipient_list',
            'smtp_config', 'enable_ai_personalization', 'scheduled_at',
        )
        extra_kwargs = {f: {'required': False} for f in fields}

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status not in ('draft', 'scheduled'):
            raise serializers.ValidationError(
                "Only draft or scheduled campaigns can be edited."
            )
        return attrs
