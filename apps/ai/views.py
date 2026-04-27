"""Views for AI service endpoints."""
import time
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_subjects(request):
    """
    POST /api/ai/generate-subjects
    Generate 5 subject line alternatives for an email body.
    """
    email_body = request.data.get('email_body', '').strip()
    context = request.data.get('context', '')

    if not email_body:
        return Response(
            {'error': 'email_body is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    start_time = time.time()
    try:
        from apps.ai.utils import generate_subject_lines
        subjects = generate_subject_lines(email_body, context)
        generation_time_ms = int((time.time() - start_time) * 1000)
        return Response({
            'subjects': subjects,
            'generation_time_ms': generation_time_ms,
        })
    except ValueError as e:
        return Response(
            {'error': f'AI service not configured: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': f'AI service error: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def spam_check(request):
    """
    POST /api/ai/spam-check
    Analyze email content for spam likelihood.
    """
    subject = request.data.get('subject', '').strip()
    body = request.data.get('body', '').strip()

    if not subject or not body:
        return Response(
            {'error': 'Both subject and body are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from apps.ai.utils import analyze_spam_score
        result = analyze_spam_score(subject, body)
        return Response(result)
    except ValueError as e:
        return Response(
            {'error': f'AI service not configured: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': f'AI service error: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def personalize(request):
    """
    POST /api/ai/personalize
    Personalize email content for recipients using AI.
    """
    from apps.templates.models import Template
    from apps.recipients.models import Recipient

    template_id = request.data.get('template_id')
    recipient_ids = request.data.get('recipient_ids', [])
    enable_personalization = request.data.get('enable_personalization', True)

    if not template_id:
        return Response({'error': 'template_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        template = Template.objects.get(id=template_id)
    except Template.DoesNotExist:
        return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)

    if not enable_personalization:
        # Template-only mode: just do variable substitution
        from apps.templates.serializers import render_template
        results = []
        for rid in recipient_ids:
            try:
                recipient = Recipient.objects.get(id=rid)
                results.append({
                    'recipient_id': str(rid),
                    'personalized_content': render_template(template.body, recipient.metadata),
                })
            except Recipient.DoesNotExist:
                pass
        return Response({'status': 'completed', 'results': results})

    # AI personalization
    try:
        from apps.ai.utils import personalize_email
        results = []
        for rid in recipient_ids:
            try:
                recipient = Recipient.objects.get(id=rid)
                personalized = personalize_email(template.body, recipient.metadata)
                results.append({
                    'recipient_id': str(rid),
                    'personalized_content': personalized,
                })
            except Recipient.DoesNotExist:
                pass
        return Response({'status': 'completed', 'results': results})
    except Exception as e:
        return Response(
            {'error': f'AI personalization failed: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
