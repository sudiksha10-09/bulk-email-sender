"""Views for recipients app."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from apps.recipients.models import RecipientList, Recipient
from apps.recipients.serializers import (
    RecipientListSerializer,
    RecipientListCreateSerializer,
    RecipientSerializer
)
from apps.recipients.utils import parse_csv_file, process_csv_recipients


class RecipientListViewSet(viewsets.ModelViewSet):
    """ViewSet for recipient list CRUD operations."""
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Return recipient lists for the current user only."""
        return RecipientList.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return RecipientListCreateSerializer
        return RecipientListSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new recipient list by uploading CSV file.
        
        POST /api/recipient-lists
        Request: multipart/form-data { name, csv_file }
        Response: { id, name, total_count, valid_count, invalid_count, status }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        name = serializer.validated_data['name']
        csv_file = serializer.validated_data['csv_file']
        
        # Parse CSV file
        csv_rows, parse_errors = parse_csv_file(csv_file)
        
        if parse_errors:
            return Response(
                {"error": parse_errors[0]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not csv_rows:
            return Response(
                {"error": "CSV file contains no valid rows"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create recipient list
        recipient_list = RecipientList.objects.create(
            user=request.user,
            name=name,
            csv_file_url=f"local://{csv_file.name}",  # For MVP, store filename; later use S3
            status='processing'
        )
        
        # Process recipients
        try:
            valid_count, invalid_count = process_csv_recipients(recipient_list, csv_rows)
            
            # Update recipient list counts
            recipient_list.total_count = valid_count + invalid_count
            recipient_list.valid_count = valid_count
            recipient_list.invalid_count = invalid_count
            recipient_list.status = 'completed'
            recipient_list.save()
            
            response_serializer = RecipientListSerializer(recipient_list)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            recipient_list.status = 'failed'
            recipient_list.save()
            return Response(
                {"error": f"Failed to process CSV: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Get recipient list with all recipients."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete recipient list and all associated recipients."""
        instance = self.get_object()
        instance.delete()
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def invalid(self, request, pk=None):
        """
        Get list of invalid emails with error reasons.
        
        GET /api/recipient-lists/{id}/invalid
        Response: [{ email, error_reason }]
        """
        recipient_list = self.get_object()
        invalid_recipients = recipient_list.recipients.filter(is_valid=False)
        
        data = [
            {
                "email": r.email,
                "error_reason": r.validation_error
            }
            for r in invalid_recipients
        ]
        
        return Response(data, status=status.HTTP_200_OK)
