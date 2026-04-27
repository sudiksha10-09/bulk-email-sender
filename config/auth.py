"""Auto-authentication for local single-user mode."""
from rest_framework.authentication import BaseAuthentication
from django.conf import settings


class LocalAutoAuthentication(BaseAuthentication):
    """
    Automatically authenticates every request as the local user.
    Only active when LOCAL_SINGLE_USER_MODE = True in settings.
    """

    def authenticate(self, request):
        if not getattr(settings, 'LOCAL_SINGLE_USER_MODE', False):
            return None

        from apps.authentication.models import User

        email = settings.LOCAL_USER_EMAIL
        password = settings.LOCAL_USER_PASSWORD

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'is_email_verified': True, 'is_active': True}
        )
        if created:
            user.set_password(password)
            user.is_email_verified = True
            user.save()

        return (user, None)
