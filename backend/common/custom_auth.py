# import jwt
# from django.utils.encoding import smart_text
# from django.utils.translation import ugettext as _
# from rest_framework import exceptions
# from rest_framework.authentication import BaseAuthentication
# from rest_framework.authentication import get_authorization_header
# import jwt
# from django.conf import settings
# from common.models import User
# #from rest_framework_jwt.settings import api_settings

# try:
#     from threading import local
# except ImportError:
#     from django.utils._threading_local import local
# _thread_locals = local()

# #jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


# # def set_current_instance_field(name, value):
# #     setattr(_thread_locals, name, value)


# # class BaseJSONWebTokenAuthentication(BaseAuthentication):
# #     """
# #     Token based authentication using the JSON Web Token standard.
# #     """
# #     print("*************************")
# #     # def authenticate(self, request):
# #     #     """
# #     #     Returns a two-tuple of User and token if a valid signature has been
# #     #     supplied using JWT-based authentication.  Otherwise returns None.
# #     #     """

# #     #     # authorization = request.META.get("HTTP_AUTHORIZATION", None)
# #     #     # self.org = request.META.get("HTTP_COMPANY", None)
# #     #     # jwt_value = self.get_jwt_value(request)
# #     #     # if jwt_value is None:
# #     #     #     return None
# #     #     # try:
# #     #     #     payload = jwt_decode_handler(jwt_value)
# #     #     # except jwt.ExpiredSignature:
# #     #     #     msg = _("Signature has expired.")
# #     #     #     raise exceptions.AuthenticationFailed(msg)
# #     #     # except jwt.DecodeError:
# #     #     #     msg = _("Error decoding signature.")
# #     #     #     raise exceptions.AuthenticationFailed(msg)
# #     #     # except jwt.InvalidTokenError:
# #     #     #     raise exceptions.AuthenticationFailed()

# #     #     # account = self.authenticate_credentials(payload)

# #     #     # set_current_instance_field("authorization", True)
# #     #     # return account, payload

# #     # def authenticate_credentials(self, payload):
# #     #     """
# #     #     Returns an active user that matches the payload's user id and email.
# #     #     """
# #     #     account_id = payload["id"]
# #     #     from common.models import User

# #     #     if not account_id:
# #     #         msg = _("Invalid payload.")
# #     #         raise exceptions.AuthenticationFailed(msg)
# #     #     try:
# #     #         account = User.objects.get(pk=account_id)

# #     #     except User.DoesNotExist:
# #     #         msg = _("Invalid signature.")
# #     #         raise exceptions.AuthenticationFailed(msg)
# #     #     return account
# #     #     # return True


# # class JSONWebTokenAuthentication(BaseJSONWebTokenAuthentication):
# #     """
# #     Clients should authenticate by passing the token key in the "Authorization"
# #     HTTP header, prepended with the string specified in the setting
# #     `JWT_AUTH_HEADER_PREFIX`. For example:
# #         Authorization: JWT eyJhbGciOiAiSFMyNTYiLCAidHlwIj
# #     """
# #     print("i am here")
# #     # www_authenticate_realm = "api"

# #     # def get_jwt_value(self, request):
# #     #     auth = get_authorization_header(request).split()
# #     #     auth_header_prefix = api_settings.JWT_AUTH_HEADER_PREFIX.lower()

# #     #     if not auth:
# #     #         if api_settings.JWT_AUTH_COOKIE:
# #     #             return request.COOKIES.get(api_settings.JWT_AUTH_COOKIE)
# #     #         return None

# #     #     if smart_text(auth[0].lower()) != auth_header_prefix:
# #     #         return None

# #     #     if len(auth) == 1:
# #     #         msg = _("Invalid Authorization header. No credentials provided.")
# #     #         raise exceptions.AuthenticationFailed(msg)
# #     #     elif len(auth) > 2:
# #     #         msg = _(
# #     #             "Invalid Authorization header. Credentials string "
# #     #             "should not contain spaces."
# #     #         )
# #     #         raise exceptions.AuthenticationFailed(msg)

# #     #     return auth[1]

# #     # def authenticate_header(self, request):
# #     #     """
# #     #     Return a string to be used as the value of the `WWW-Authenticate`
# #     #     header in a `401 Unauthenticated` response, or `None` if the
# #     #     authentication scheme should return `403 Permission Denied` responses.
# #     #     """
# #     #     return '{0} realm="{1}"'.format(
# #     #         api_settings.JWT_AUTH_HEADER_PREFIX, self.www_authenticate_realm
# #     #     )


# # class TokenAuthMiddleware(object):
# #     """adding profile and company to request object"""

# #     def __init__(self, get_response):
# #         self.get_response = get_response

# #     def __call__(self, request):
# #         self.process_request(request)
# #         return self.get_response(request)

# #     def process_request(self, request):
# #         try:
# #             token_auth_user = JSONWebTokenAuthentication().authenticate(request)
# #         except exceptions.AuthenticationFailed:
# #             token_auth_user = None
# #         if isinstance(token_auth_user, tuple):
# #             request.user = token_auth_user[0]


# class JSONWebTokenAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         if not request.headers.get("Authorization"):
#             raise exceptions.AuthenticationFailed('Access Token is not Provided!')
#         else:
#             token1=(request.headers.get("Authorization"))
#             token=(token1.split(' ')[1])# getting the token value
#             decoded = jwt.decode(token, settings.SECRET_KEY)
#             user=User.objects.filter(id=decoded['user_id']).first()

#             return (user, None)
