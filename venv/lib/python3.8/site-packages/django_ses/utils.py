import base64
import logging
import warnings
from builtins import bytes

from django_ses.deprecation import RemovedInDjangoSES20Warning

from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import URLError

from django.core.exceptions import ImproperlyConfigured
from django_ses import settings

logger = logging.getLogger(__name__)

_CERT_CACHE = {}


def clear_cert_cache():
    """Clear the certificate cache.

    This one-liner exists to discourage imports and direct usage of
    _CERT_CACHE.

    :returns None
    """
    _CERT_CACHE.clear()


class EventMessageVerifier(object):
    """
    A utility class for validating event messages

    See: http://docs.amazonwebservices.com/sns/latest/gsg/SendMessageToHttp.verify.signature.html
    """

    _REQ_DEP_TMPL = (
        "%s is required for event message verification. Please install "
        "`django-ses` with the `event` extra - e.g. "
        "`pip install django-ses[events]`."
    )

    def __init__(self, notification):
        """
        Creates a new event message from the given dict.
        """
        self._data = notification
        self._verified = None

    def is_verified(self):
        """
        Verifies an SES event message.

        Sign the bytes from the notification and compare it to the signature in
        the notification. If same, return True; else False.
        """
        if self._verified is not None:
            return self._verified

        signature = self._data.get("Signature")
        if not signature:
            self._verified = False
            return self._verified

        # Decode the signature from base64
        signature = bytes(base64.b64decode(signature))

        # Get the message to sign
        sign_bytes = self._get_bytes_to_sign()
        if not sign_bytes:
            self._verified = False
            return self._verified

        if not self.certificate:
            self._verified = False
            return self._verified

        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
        except ImportError:
            raise ImproperlyConfigured(self._REQ_DEP_TMPL % "`cryptography`")

        # Extract the public key
        pkey = self.certificate.public_key()

        # Use the public key to verify the signature.
        try:
            # The details here do not appear to be documented, but the
            # algorithm and padding choices work in testing, which should mean
            # they're the right ones.
            pkey.verify(
                signature,
                sign_bytes,
                padding.PKCS1v15(),
                hashes.SHA1(),
            )
        except InvalidSignature:
            logger.warning(
                "Invalid signature on message with ID: %s",
                self._data.get("MessageId"),
            )
            self._verified = False
        else:
            self._verified = True
        return self._verified

    @property
    def certificate(self):
        """
        Retrieves the certificate used to sign the event message.

        :returns: None if the cert cannot be retrieved. Else, gets the cert
        caches it, and returns it, or simply returns it if already cached.
        """
        cert_url = self._get_cert_url()
        if not cert_url:
            return None

        if cert_url in _CERT_CACHE:
            return _CERT_CACHE[cert_url]

        # Only load certificates from a certain domain?
        # Without some kind of trusted domain check, any old joe could
        # craft a event message and sign it using his own certificate
        # and we would happily load and verify it.
        try:
            import requests
            from requests import RequestException
        except ImportError:
            raise ImproperlyConfigured(self._REQ_DEP_TMPL % "`requests`")

        try:
            from cryptography import x509
        except ImportError:
            raise ImproperlyConfigured(self._REQ_DEP_TMPL % "`cryptography`")

        # We use requests because it verifies the https certificate when
        # retrieving the signing certificate. If https was somehow hijacked
        # then all bets are off.
        try:
            response = requests.get(cert_url, timeout=10)
            response.raise_for_status()
        except RequestException as exc:
            logger.warning(
                "Network error downloading certificate from " "%s: %s",
                cert_url,
                exc,
            )
            _CERT_CACHE[cert_url] = None
            return _CERT_CACHE[cert_url]

        # Handle errors loading the certificate.
        # If the certificate is invalid then return
        # false as we couldn't verify the message.
        try:
            _CERT_CACHE[cert_url] = x509.load_pem_x509_certificate(response.content)
        except ValueError as e:
            logger.warning('Could not load certificate from %s: "%s"', cert_url, e)
            _CERT_CACHE[cert_url] = None

        return _CERT_CACHE[cert_url]

    def _get_cert_url(self):
        """
        Get the signing certificate URL.
        Only accept urls that match the domains set in the
        AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS setting. Sub-domains
        are allowed. i.e. if amazonaws.com is in the trusted domains
        then sns.us-east-1.amazonaws.com will match.
        """
        cert_url = self._data.get("SigningCertURL")
        if not cert_url:
            logger.warning('No signing certificate URL: "%s"', cert_url)
            return None

        if not cert_url.startswith("https://"):
            logger.warning('Untrusted certificate URL: "%s"', cert_url)
            return None

        url_obj = urlparse(cert_url)
        for trusted_domain in settings.EVENT_CERT_DOMAINS:
            parts = trusted_domain.split(".")
            if url_obj.netloc.split(".")[-len(parts) :] == parts:
                return cert_url

        return None

    def _get_bytes_to_sign(self):
        """
        Creates the message used for signing SNS notifications.
        This is used to verify the bounce message when it is received.
        """

        # Depending on the message type the fields to add to the message
        # differ so we handle that here.
        msg_type = self._data.get('Type')
        if msg_type == 'Notification':
            fields_to_sign = [
                'Message',
                'MessageId',
                'Subject',
                'Timestamp',
                'TopicArn',
                'Type',
            ]
        elif (msg_type == 'SubscriptionConfirmation' or
              msg_type == 'UnsubscribeConfirmation'):
            fields_to_sign = [
                'Message',
                'MessageId',
                'SubscribeURL',
                'Timestamp',
                'Token',
                'TopicArn',
                'Type',
            ]
        else:
            # Unrecognized type
            logger.warning('Unrecognized SNS message Type: "%s"', msg_type)
            return None

        bytes_to_sign = []
        for field in fields_to_sign:
            field_value = self._data.get(field)
            if not field_value:
                continue

            # Some notification types do not have all fields. Only add fields
            # with values.
            bytes_to_sign.append(f"{field}\n{field_value}\n")

        return "".join(bytes_to_sign).encode()


def BounceMessageVerifier(*args, **kwargs):
    warnings.warn(
        'utils.BounceMessageVerifier is deprecated. It is renamed to EventMessageVerifier.',
        RemovedInDjangoSES20Warning,
    )

    # parameter name is renamed from bounce_dict to notification.
    if 'bounce_dict' in kwargs:
        kwargs['notification'] = kwargs['bounce_dict']
        del kwargs['bounce_dict']

    return EventMessageVerifier(*args, **kwargs)


def verify_event_message(notification):
    """
    Verify an SES/SNS event notification message.
    """
    verifier = EventMessageVerifier(notification)
    return verifier.is_verified()


def verify_bounce_message(msg):
    """
    Verify an SES/SNS bounce(event) notification message.
    """
    warnings.warn(
        'utils.verify_bounce_message is deprecated. It is renamed to verify_event_message.',
        RemovedInDjangoSES20Warning,
    )
    return verify_event_message(msg)


def confirm_sns_subscription(notification):
    logger.info(
        'Received subscription confirmation: TopicArn: %s',
        notification.get('TopicArn'),
        extra={
            'notification': notification,
        },
    )

    # Get the subscribe url and hit the url to confirm the subscription.
    subscribe_url = notification.get('SubscribeURL')
    try:
        urlopen(subscribe_url).read()
    except URLError as e:
        # Some kind of error occurred when confirming the request.
        logger.error(
            'Could not confirm subscription: "%s"', e,
            extra={
                'notification': notification,
            },
            exc_info=True,
        )
