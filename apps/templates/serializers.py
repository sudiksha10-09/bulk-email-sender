"""Serializers for templates app."""
import re
from rest_framework import serializers
from apps.templates.models import Template


def validate_template_variables(text):
    """
    Validate {{variable}} syntax in template text.
    Returns list of error messages (empty if valid).
    """
    errors = []
    # Check for unmatched braces
    open_count = text.count('{{')
    close_count = text.count('}}')
    if open_count != close_count:
        errors.append(f"Unmatched template braces: {open_count} opening '{{{{' vs {close_count} closing '}}}}'")
        return errors

    # Validate variable names inside {{ }}
    var_pattern = re.compile(r'\{\{([^}]+)\}\}')
    for match in var_pattern.finditer(text):
        var_name = match.group(1).strip()
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
            errors.append(
                f"Invalid variable name '{{{{ {var_name} }}}}': must be a valid identifier "
                "(letters, numbers, underscores, starting with letter or underscore)"
            )
    return errors


def extract_variables(text):
    """Extract all {{variable}} names from template text."""
    pattern = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    return list(set(pattern.findall(text)))


def render_template(text, context):
    """
    Render template by replacing {{variable}} with values from context dict.
    Handles both plain text and HTML bodies. Missing variables are left as-is.
    """
    import html as html_module

    # Decode any HTML entities first (e.g. &#123;&#123; → {{)
    text = html_module.unescape(text)

    def replace_var(match):
        var_name = match.group(1).strip()
        return str(context.get(var_name, match.group(0)))

    return re.sub(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}', replace_var, text)


class TemplateSerializer(serializers.ModelSerializer):
    """Full template serializer for read operations."""

    class Meta:
        model = Template
        fields = ('id', 'name', 'subject', 'body', 'variables', 'version', 'created_at', 'updated_at')
        read_only_fields = ('id', 'version', 'created_at', 'updated_at')


class TemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing templates."""

    class Meta:
        model = Template
        fields = ('id', 'name', 'subject', 'version', 'created_at', 'updated_at')
        read_only_fields = ('id', 'version', 'created_at', 'updated_at')


class TemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating templates."""

    class Meta:
        model = Template
        fields = ('name', 'subject', 'body', 'variables')

    def validate_subject(self, value):
        errors = validate_template_variables(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate_body(self, value):
        errors = validate_template_variables(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def create(self, validated_data):
        # Auto-extract variables from subject + body
        subject = validated_data.get('subject', '')
        body = validated_data.get('body', '')
        all_vars = list(set(extract_variables(subject) + extract_variables(body)))
        validated_data['variables'] = all_vars
        return super().create(validated_data)


class TemplateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating templates (increments version)."""

    class Meta:
        model = Template
        fields = ('name', 'subject', 'body', 'variables')
        extra_kwargs = {
            'name': {'required': False},
            'subject': {'required': False},
            'body': {'required': False},
            'variables': {'required': False},
        }

    def validate_subject(self, value):
        errors = validate_template_variables(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate_body(self, value):
        errors = validate_template_variables(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def update(self, instance, validated_data):
        # Re-extract variables if subject or body changed
        subject = validated_data.get('subject', instance.subject)
        body = validated_data.get('body', instance.body)
        validated_data['variables'] = list(set(extract_variables(subject) + extract_variables(body)))
        # Increment version on every update
        validated_data['version'] = instance.version + 1
        return super().update(instance, validated_data)


class TemplatePreviewSerializer(serializers.Serializer):
    """Serializer for template preview request."""
    sample_data = serializers.DictField(child=serializers.CharField(), required=False, default=dict)
