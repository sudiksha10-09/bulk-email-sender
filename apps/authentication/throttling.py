"""Custom throttling classes for authentication endpoints."""
from rest_framework.throttling import AnonRateThrottle


class AuthenticationThrottle(AnonRateThrottle):
    """
    Rate limiting for authentication endpoints.
    Limits to 5 attempts per minute per IP address.
    """
    rate = '5/minute'
    
    def get_cache_key(self, request, view):
        """Generate cache key based on IP address."""
        if request.user.is_authenticated:
            return None  # Don't throttle authenticated users
        
        # Get client IP address
        ip_address = self.get_ident(request)
        return f'auth_throttle_{ip_address}'
