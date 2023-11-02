import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from common.models import Org,Profile,User
from django.conf import settings

def verify_jwt_token(token1):
    secret_key = (settings.SECRET_KEY) # Replace with your secret key used for token encoding/decoding
    try:
        token = token1.split(" ")[1]  # getting the token value
        payload = jwt.decode(token, (settings.SECRET_KEY), algorithms=[settings.JWT_ALGO])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token is expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"

class CustomDualAuthentication(BaseAuthentication):

    def authenticate(self, request: Request):

        jwt_user = None
        profile = None
        # Check JWT authentication
        # Implement your JWT authentication logic here
        # You might use a library like `python_jwt` to decode and verify the JWT token
        # Example code assumes a method `verify_jwt_token` for JWT verification
        jwt_token = request.META.get('HTTP_AUTHORIZATION')
        if jwt_token:
            is_valid, jwt_payload = verify_jwt_token(jwt_token)
            if is_valid:
                # JWT authentication successful
                jwt_user = (User.objects.get(id=jwt_payload['user_id']),True)
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
                # API key authentication successful
                api_key_user = organization
                request.META['org'] = api_key_user.id
                profile = Profile.objects.filter(org=api_key_user,role="ADMIN").first()
                request.profile = profile
                profile = (profile.user,True)
            except Org.DoesNotExist:
                raise AuthenticationFailed('Invalid API Key')
        # Select the appropriate user based on authentication method
        # Return the user if any authentication method succeeded
        return jwt_user or profile
