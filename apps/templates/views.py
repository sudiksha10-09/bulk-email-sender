"""Views for templates app."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.templates.models import Template
from apps.templates.serializers import (
    TemplateSerializer,
    TemplateListSerializer,
    TemplateCreateSerializer,
    TemplateUpdateSerializer,
    TemplatePreviewSerializer,
    render_template,
)


class TemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for email template CRUD operations."""

    permission_classes = [AllowAny]

    def get_queryset(self):
        return Template.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return TemplateListSerializer
        if self.action == 'create':
            return TemplateCreateSerializer
        if self.action in ('update', 'partial_update'):
            return TemplateUpdateSerializer
        return TemplateSerializer

    def create(self, request, *args, **kwargs):
        """POST /api/templates"""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Template create request data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Template validation errors: {serializer.errors}")
        serializer.is_valid(raise_exception=True)
        template = serializer.save(user=None)  # No user required
        return Response(TemplateSerializer(template).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """PUT/PATCH /api/templates/{id}"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()
        return Response(TemplateSerializer(template).data)

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/templates/{id}"""
        instance = self.get_object()
        instance.delete()
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        POST /api/templates/{id}/preview
        Render template with sample data.
        """
        template = self.get_object()
        serializer = TemplatePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sample_data = serializer.validated_data.get('sample_data', {})

        rendered_subject = render_template(template.subject, sample_data)
        rendered_body = render_template(template.body, sample_data)

        return Response({
            'rendered_subject': rendered_subject,
            'rendered_body': rendered_body,
        })

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        POST /api/templates/{id}/duplicate
        Create a copy of the template.
        """
        original = self.get_object()
        duplicate = Template.objects.create(
            user=None,  # No user required
            name=f"Copy of {original.name}",
            subject=original.subject,
            body=original.body,
            variables=original.variables,
            version=1,
        )
        return Response(TemplateSerializer(duplicate).data, status=status.HTTP_201_CREATED)
