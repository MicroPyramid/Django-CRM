import jwt
from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response

from common.models import Org, Profile, User


def set_profile_request(request, org, token):
    # we are decoding the token
    decoded = jwt.decode(token, (settings.SECRET_KEY), algorithms=[settings.JWT_ALGO])

    request.user = User.objects.get(id=decoded["user_id"])

    if request.user:
        request.profile = Profile.objects.get(
            user=request.user, org=org, is_active=True
        )
        request.profile.role = "ADMIN"
        request.profile.save()
        if request.profile is None:
            logout(request)
            return Response(
                {"error": False},
                status=status.HTTP_200_OK,
            )


class GetProfileAndOrg(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):

        # here I am getting the the jwt token passing in header
        if request.headers.get("Authorization"):
            token1 = request.headers.get("Authorization")

            token = token1.split(" ")[1]  # getting the token value
            if request.headers.get("org"):
                org_id = request.headers.get("org")
                org = Org.objects.get(id=org_id)
                if org:
                    request.org = org
                    set_profile_request(request, org, token)
                else:
                    request.org = None
            else:
                request.org = None
