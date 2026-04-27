"""Stripe billing views."""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe(request):
    """
    POST /api/billing/subscribe/
    Create a Stripe subscription for the authenticated user.
    Body: { "payment_method_id": "pm_...", "price_id": "price_...", "email": "..." }
    """
    try:
        import stripe
    except ImportError:
        return Response(
            {'error': 'Stripe not installed. Run: pip install stripe'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    if not stripe.api_key:
        return Response(
            {'error': 'Stripe not configured. Set STRIPE_SECRET_KEY in .env'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    payment_method_id = request.data.get('payment_method_id')
    price_id = request.data.get('price_id')
    email = request.data.get('email') or request.user.email

    if not payment_method_id or not price_id:
        return Response(
            {'error': 'payment_method_id and price_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get or create Stripe customer
        customer_id = getattr(request.user, 'stripe_customer_id', None)
        if not customer_id:
            customer = stripe.Customer.create(
                email=email,
                payment_method=payment_method_id,
                invoice_settings={'default_payment_method': payment_method_id},
            )
            customer_id = customer.id
            # Store on user if field exists
            try:
                request.user.stripe_customer_id = customer_id
                request.user.save(update_fields=['stripe_customer_id'])
            except Exception:
                pass
        else:
            stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_method_id},
            )

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': price_id}],
            expand=['latest_invoice.payment_intent'],
        )

        invoice = subscription.latest_invoice
        payment_intent = invoice.payment_intent if invoice else None

        if payment_intent and payment_intent.status == 'requires_action':
            return Response({
                'requires_action': True,
                'client_secret': payment_intent.client_secret,
            })

        return Response({
            'success': True,
            'subscription_id': subscription.id,
            'status': subscription.status,
        })

    except stripe.error.CardError as e:
        return Response({'error': e.user_message}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return Response({'error': 'Payment failed. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Billing error: {e}")
        return Response({'error': 'An error occurred processing your payment.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """POST /api/billing/cancel/ — Cancel active subscription."""
    try:
        import stripe
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        subscription_id = request.data.get('subscription_id')
        if not subscription_id:
            return Response({'error': 'subscription_id required'}, status=status.HTTP_400_BAD_REQUEST)
        stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        return Response({'success': True, 'message': 'Subscription will cancel at end of billing period.'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
