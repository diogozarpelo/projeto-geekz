from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        ttl_hours = settings.AUTH_TOKEN_TTL_HOURS

        if ttl_hours > 0:
            expires_at = (
                token.created
                + timedelta(hours=ttl_hours)
            )

            if timezone.now() >= expires_at:
                token.delete()

                raise AuthenticationFailed(
                    "Authentication token has expired."
                )

        return user, token
