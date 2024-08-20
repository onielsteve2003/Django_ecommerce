from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                raise AuthenticationFailed('Invalid token header. No credentials provided.')

            # Decode the token and get user info
            decoded_token = AccessToken(token)
            user_id = decoded_token.get('user_id')
            user = get_user_model().objects.get(id=user_id)
        except (ValueError, get_user_model().DoesNotExist):
            raise AuthenticationFailed('Invalid token.')

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'
