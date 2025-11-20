import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from common.models import Org,Profile,User
from django.conf import settings

def verify_jwt_token(token):
    secret_key = (settings.SECRET_KEY) # Replace with your secret key used for token encoding/decoding
    try:
        payload = jwt.decode(token, (settings.SECRET_KEY), algorithms=[settings.JWT_ALGO])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token is expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"

class CustomDualAuthentication(BaseAuthentication):

    def authenticate(self, request):
        jwt_user = None
        profile = None

        # Check JWT authentication
        jwt_token = request.headers.get('Authorization', '').split(' ')[1] if 'Authorization' in request.headers else None
        if jwt_token:
            is_valid, jwt_payload = verify_jwt_token(jwt_token)
            if is_valid:
                jwt_user = (User.objects.get(id=jwt_payload['user_id']), True)
                if jwt_payload['user_id'] is not None:
                    if request.headers.get("org"):
                        profile = Profile.objects.get(
                            user_id=jwt_payload['user_id'], org=request.headers.get("org"), is_active=True
                        )
                        if profile:
                            request.profile = profile

        # Check API key authentication
        api_key = request.headers.get('Token')  # Get API key from request query params
        if api_key:
            try:
                organization = Org.objects.get(api_key=api_key)
                api_key_user = organization
                request.META['org'] = api_key_user.id
                profile = Profile.objects.filter(org=api_key_user, role="ADMIN").first()
                request.profile = profile
                profile = (profile.user, True)
            except Org.DoesNotExist:
                raise AuthenticationFailed('Invalid API Key')

        # Select the appropriate user based on authentication method
        # Return the user if any authentication method succeeded
        return jwt_user or profile
