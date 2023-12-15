import jwt
from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import ValidationError,PermissionDenied
from rest_framework import status
from rest_framework.response import Response
from crum import get_current_user
from django.utils.functional import SimpleLazyObject

from common.models import Org, Profile, User


# def set_profile_request(request, org, token):
#     # we are decoding the token
#     decoded = jwt.decode(token, (settings.SECRET_KEY), algorithms=[settings.JWT_ALGO])

#     request.user = User.objects.get(id=decoded["user_id"])

#     if request.user:
#         request.profile = Profile.objects.get(
#             user=request.user, org=org, is_active=True
#         )
#         request.profile.role = "ADMIN"
#         request.profile.save()
#         if request.profile is None:
#             logout(request)
#             return Response(
#                 {"error": False},
#                 status=status.HTTP_200_OK,
            # )

def get_actual_value(request):
    if request.user is None:
        return None

    return request.user #here should have value, so any code using request.user will work

class GetProfileAndOrg(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        try :
            request.profile = None
            user_id = None
            # here I am getting the the jwt token passing in header
            if request.headers.get("Authorization"):
                token1 = request.headers.get("Authorization")
                token = token1.split(" ")[1]  # getting the token value
                decoded = jwt.decode(token, (settings.SECRET_KEY), algorithms=[settings.JWT_ALGO])
                user_id = decoded['user_id']
            api_key = request.headers.get('Token')  # Get API key from request query params
            if api_key:
                try:
                    organization = Org.objects.get(api_key=api_key)
                    api_key_user = organization
                    request.META['org'] = api_key_user.id
                    profile = Profile.objects.filter(org=api_key_user, role="ADMIN").first()
                    user_id = profile.user.id
                except Org.DoesNotExist:
                    raise AuthenticationFailed('Invalid API Key')
            if user_id is not None:
                if request.headers.get("org"):
                    profile = Profile.objects.get(
                        user_id=user_id, org=request.headers.get("org"), is_active=True
                    )
                    if profile:
                        request.profile = profile
        except :
             print('test1')
             raise PermissionDenied()
