"""Custom DRF exception handler for consistent error responses."""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# Sensitive fields to redact from logs
_SENSITIVE_FIELDS = {'password', 'token', 'access', 'refresh', 'encrypted_password', 'api_key'}


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error format:
    { "error": "<message>", "detail": <optional detail> }

    Also logs errors with context, redacting sensitive data.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Normalize to { error, detail } shape
        data = response.data
        if isinstance(data, dict):
            # DRF often returns {'detail': '...'} — normalize it
            if 'detail' in data and len(data) == 1:
                response.data = {'error': str(data['detail'])}
            elif 'non_field_errors' in data:
                response.data = {'error': data['non_field_errors'][0] if data['non_field_errors'] else 'Validation error'}
            else:
                # Flatten field errors into a readable message
                errors = {}
                for field, messages in data.items():
                    if isinstance(messages, list):
                        errors[field] = messages[0] if messages else ''
                    else:
                        errors[field] = str(messages)
                response.data = {'error': 'Validation failed', 'detail': errors}
        elif isinstance(data, list):
            response.data = {'error': data[0] if data else 'Unknown error'}

        # Log 5xx errors with context
        if response.status_code >= 500:
            request = context.get('request')
            view = context.get('view')
            safe_data = _redact_sensitive(getattr(request, 'data', {}))
            logger.error(
                f"Server error in {view.__class__.__name__ if view else 'unknown'}: "
                f"{exc} | request_data={safe_data}",
                exc_info=exc,
            )

    return response


def _redact_sensitive(data):
    """Return a copy of data with sensitive fields replaced by [REDACTED]."""
    if not isinstance(data, dict):
        return data
    return {
        k: '[REDACTED]' if k.lower() in _SENSITIVE_FIELDS else v
        for k, v in data.items()
    }
