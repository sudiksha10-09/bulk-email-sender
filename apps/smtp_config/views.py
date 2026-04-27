"""Views for SMTP configuration app."""
import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.smtp_config.models import SMTPConfig
from apps.smtp_config.serializers import (
    SMTPConfigSerializer,
    SMTPConfigCreateSerializer,
    SMTPConfigUpdateSerializer
)
from apps.smtp_config.utils import encrypt_password, decrypt_password, test_smtp_connection

logger = logging.getLogger(__name__)


class SMTPConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for SMTP configuration CRUD operations."""
    
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Return all SMTP configs (no user filtering)."""
        return SMTPConfig.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return SMTPConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SMTPConfigUpdateSerializer
        return SMTPConfigSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new SMTP configuration."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Encrypt password before saving
            password = serializer.validated_data.pop('password')
            encrypted_password = encrypt_password(password)
            
            # Create SMTP config
            smtp_config = SMTPConfig.objects.create(
                user=None,  # No user required
                encrypted_password=encrypted_password,
                **serializer.validated_data
            )
            
            # Return response
            response_serializer = SMTPConfigSerializer(smtp_config)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating SMTP config: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """Update an existing SMTP configuration."""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # Handle password update if provided
            if 'password' in serializer.validated_data:
                password = serializer.validated_data.pop('password')
                if password:  # Only update if password is not empty
                    instance.encrypted_password = encrypt_password(password)
                    instance.is_validated = False  # Require re-validation after password change
            
            # Update other fields
            for attr, value in serializer.validated_data.items():
                setattr(instance, attr, value)
            
            instance.save()
            
            response_serializer = SMTPConfigSerializer(instance)
            return Response(response_serializer.data)
        except Exception as e:
            logger.error(f"Error updating SMTP config: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete an SMTP configuration."""
        instance = self.get_object()
        instance.delete()
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)

    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test SMTP configuration by sending a test email.
        
        POST /api/smtp-configs/{id}/test
        Request body: { "test_email": "user@example.com" } (optional, defaults to user's email)
        Response: { "success": true/false, "message": "..." }
        """
        smtp_config = self.get_object()
        
        # Test the SMTP connection
        success, message = test_smtp_connection(smtp_config)
        
        if success:
            # Mark as validated
            smtp_config.is_validated = True
            smtp_config.save()
            
            return Response({
                "success": True,
                "message": message
            }, status=status.HTTP_200_OK)
        else:
            # Mark as not validated
            smtp_config.is_validated = False
            smtp_config.save()
            
            return Response({
                "success": False,
                "message": message
            }, status=status.HTTP_400_BAD_REQUEST)
