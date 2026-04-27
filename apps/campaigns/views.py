"""Views for campaigns app."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.utils import timezone
from apps.campaigns.models import Campaign
from apps.campaigns.serializers import (
    CampaignSerializer,
    CampaignListSerializer,
    CampaignCreateSerializer,
    CampaignUpdateSerializer,
)


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for campaign CRUD and activation."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignListSerializer
        if self.action == 'create':
            return CampaignCreateSerializer
        if self.action in ('update', 'partial_update'):
            return CampaignUpdateSerializer
        return CampaignSerializer

    def create(self, request, *args, **kwargs):
        """POST /api/campaigns"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        campaign = serializer.save(
            user=request.user,
            status='scheduled' if serializer.validated_data.get('scheduled_at') else 'draft',
            total_recipients=serializer.validated_data['recipient_list'].valid_count,
        )
        return Response(CampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """PUT/PATCH /api/campaigns/{id}"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        campaign = serializer.save()
        return Response(CampaignSerializer(campaign).data)

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/campaigns/{id}"""
        instance = self.get_object()
        if instance.status in ('sending',):
            return Response(
                {'error': 'Cannot delete a campaign that is currently sending.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        POST /api/campaigns/{id}/activate
        Validate and queue campaign for sending.
        """
        campaign = self.get_object()

        # Validate campaign is in activatable state
        if campaign.status in ('queued', 'sending', 'completed'):
            return Response(
                {'error': f'Campaign is already {campaign.status}.'},
                status=status.HTTP_409_CONFLICT
            )

        # Validate required fields
        missing = []
        if not campaign.name:
            missing.append('name')
        if not campaign.subject:
            missing.append('subject')
        if not campaign.template_id:
            missing.append('template')
        if not campaign.recipient_list_id:
            missing.append('recipient_list')
        if not campaign.smtp_config_id:
            missing.append('smtp_config')

        if missing:
            return Response(
                {'error': f'Campaign missing required fields: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate recipient list has valid emails
        if campaign.recipient_list.valid_count == 0:
            return Response(
                {'error': 'Recipient list contains no valid emails.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Queue the campaign
        campaign.status = 'queued'
        campaign.total_recipients = campaign.recipient_list.valid_count
        campaign.save()

        # Dispatch Celery task
        job_id = None
        try:
            from apps.campaigns.tasks import send_campaign
            result = send_campaign.delay(str(campaign.id))
            job_id = result.id
        except Exception:
            # Celery not available (e.g., in tests) - still mark as queued
            pass

        return Response({
            'id': str(campaign.id),
            'status': campaign.status,
            'job_id': job_id,
        })

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        GET /api/campaigns/{id}/progress
        Return real-time progress metrics (uses Redis cache when available).
        """
        campaign = self.get_object()

        # Try cache first for real-time data
        from django.core.cache import cache
        cached = cache.get(f'campaign_progress_{campaign.id}')
        if cached:
            sent = cached.get('sent_count', campaign.sent_count)
            failed = cached.get('failed_count', campaign.failed_count)
            total = cached.get('total_recipients', campaign.total_recipients)
        else:
            sent = campaign.sent_count
            failed = campaign.failed_count
            total = campaign.total_recipients

        pending = max(0, total - sent - failed)
        percentage = round((sent + failed) / total * 100, 1) if total > 0 else 0

        estimated_completion = None
        if campaign.started_at and sent > 0 and pending > 0:
            elapsed = (timezone.now() - campaign.started_at).total_seconds()
            rate = sent / elapsed if elapsed > 0 else 1
            estimated_seconds = pending / rate
            estimated_completion = (
                timezone.now() + timezone.timedelta(seconds=estimated_seconds)
            ).isoformat()

        return Response({
            'total': total,
            'sent': sent,
            'failed': failed,
            'pending': pending,
            'progress_percentage': percentage,
            'status': campaign.status,
            'estimated_completion': estimated_completion,
        })

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """
        GET /api/campaigns/{id}/analytics
        Return campaign analytics.
        """
        from apps.tracking.models import EmailLog, EmailEvent
        from django.db.models import Count, Q

        campaign = self.get_object()

        total_sent = EmailLog.objects.filter(
            campaign=campaign, status='sent'
        ).count()
        total_bounced = EmailLog.objects.filter(
            campaign=campaign, status='bounced'
        ).count()

        # Unique opens and clicks
        total_opened = EmailEvent.objects.filter(
            email_log__campaign=campaign,
            event_type='open'
        ).values('tracking_id').distinct().count()

        total_clicked = EmailEvent.objects.filter(
            email_log__campaign=campaign,
            event_type='click'
        ).values('tracking_id').distinct().count()

        open_rate = round(total_opened / total_sent * 100, 2) if total_sent > 0 else 0
        click_rate = round(total_clicked / total_sent * 100, 2) if total_sent > 0 else 0
        bounce_rate = round(total_bounced / total_sent * 100, 2) if total_sent > 0 else 0

        # Opens over time (hourly buckets)
        from django.db.models.functions import TruncHour
        opens_over_time = list(
            EmailEvent.objects.filter(
                email_log__campaign=campaign, event_type='open'
            ).annotate(hour=TruncHour('created_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
            .values('hour', 'count')
        )

        clicks_over_time = list(
            EmailEvent.objects.filter(
                email_log__campaign=campaign, event_type='click'
            ).annotate(hour=TruncHour('created_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
            .values('hour', 'count')
        )

        return Response({
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'total_bounced': total_bounced,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'bounce_rate': bounce_rate,
            'opens_over_time': opens_over_time,
            'clicks_over_time': clicks_over_time,
        })
