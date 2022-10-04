import logging

import boto3
from botocore.vendored.requests.packages.urllib3.exceptions import ResponseError
from django.core.mail.backends.base import BaseEmailBackend
from django_ses import settings

from datetime import datetime, timedelta
from time import sleep


try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    # Shim for Python 3.7. Remove when support is dropped.
    import importlib_metadata

__version__ = importlib_metadata.version(__name__)
__all__ = ('SESBackend',)

# These would be nice to make class-level variables, but the backend is
# re-created for each outgoing email/batch.
# recent_send_times also is not going to work quite right if there are multiple
# email backends with different rate limits returned by SES, but that seems
# like it would be rare.
cached_rate_limits = {}
recent_send_times = []

logger = logging.getLogger('django_ses')


def dkim_sign(message, dkim_domain=None, dkim_key=None, dkim_selector=None, dkim_headers=None):
    """Return signed email message if dkim package and settings are available."""
    try:
        import dkim
    except ImportError:
        pass
    else:
        if dkim_domain and dkim_key:
            sig = dkim.sign(message,
                            dkim_selector,
                            dkim_domain,
                            dkim_key,
                            include_headers=dkim_headers)
            message = sig + message
    return message


def cast_nonzero_to_float(val):
    """Cast nonzero number to float; on zero or None, return None"""
    if not val:
        return None
    return float(val)


class SESBackend(BaseEmailBackend):
    """A Django Email backend that uses Amazon's Simple Email Service.
    """

    def __init__(self, fail_silently=False, aws_access_key=None,
                 aws_secret_key=None, aws_session_token=None, aws_region_name=None,
                 aws_region_endpoint=None, aws_auto_throttle=None, aws_config=None,
                 dkim_domain=None, dkim_key=None, dkim_selector=None, dkim_headers=None,
                 ses_source_arn=None, ses_from_arn=None, ses_return_path_arn=None,
                 **kwargs):

        super(SESBackend, self).__init__(fail_silently=fail_silently, **kwargs)
        self._access_key_id = aws_access_key or settings.ACCESS_KEY
        self._access_key = aws_secret_key or settings.SECRET_KEY
        self._session_token = aws_session_token or settings.SESSION_TOKEN
        self._region_name = aws_region_name if aws_region_name else settings.AWS_SES_REGION_NAME
        self._endpoint_url = aws_region_endpoint if aws_region_endpoint else settings.AWS_SES_REGION_ENDPOINT_URL
        self._throttle = cast_nonzero_to_float(aws_auto_throttle or settings.AWS_SES_AUTO_THROTTLE)
        self._config = aws_config or settings.AWS_SES_CONFIG

        self.dkim_domain = dkim_domain or settings.DKIM_DOMAIN
        self.dkim_key = dkim_key or settings.DKIM_PRIVATE_KEY
        self.dkim_selector = dkim_selector or settings.DKIM_SELECTOR
        self.dkim_headers = dkim_headers or settings.DKIM_HEADERS

        self.ses_source_arn = ses_source_arn or settings.AWS_SES_SOURCE_ARN
        self.ses_from_arn = ses_from_arn or settings.AWS_SES_FROM_ARN
        self.ses_return_path_arn = ses_return_path_arn or settings.AWS_SES_RETURN_PATH_ARN

        self.connection = None

    def open(self):
        """Create a connection to the AWS API server. This can be reused for
        sending multiple emails.
        """
        if self.connection:
            return False

        try:
            self.connection = boto3.client(
                'ses',
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._access_key,
                aws_session_token=self._session_token,
                region_name=self._region_name,
                endpoint_url=self._endpoint_url,
                config=self._config
            )

        except Exception:
            if not self.fail_silently:
                raise

    def close(self):
        """Close any open HTTP connections to the API server.
        """
        self.connection = None

    def send_messages(self, email_messages):
        """Sends one or more EmailMessage objects and returns the number of
        email messages sent.
        """
        if not email_messages:
            return

        new_conn_created = self.open()
        if not self.connection:
            # Failed silently
            return

        num_sent = 0
        source = settings.AWS_SES_RETURN_PATH
        for message in email_messages:
            # SES Configuration sets. If the AWS_SES_CONFIGURATION_SET setting
            # is not None, append the appropriate header to the message so that
            # SES knows which configuration set it belongs to.
            #
            # If settings.AWS_SES_CONFIGURATION_SET is a callable, pass it the
            # message object and dkim settings and expect it to return a string
            # containing the SES Configuration Set name.
            if (settings.AWS_SES_CONFIGURATION_SET
                    and 'X-SES-CONFIGURATION-SET' not in message.extra_headers):
                if callable(settings.AWS_SES_CONFIGURATION_SET):
                    message.extra_headers[
                        'X-SES-CONFIGURATION-SET'] = settings.AWS_SES_CONFIGURATION_SET(
                            message,
                            dkim_domain=self.dkim_domain,
                            dkim_key=self.dkim_key,
                            dkim_selector=self.dkim_selector,
                            dkim_headers=self.dkim_headers
                        )
                else:
                    message.extra_headers[
                        'X-SES-CONFIGURATION-SET'] = settings.AWS_SES_CONFIGURATION_SET

            # Automatic throttling. Assumes that this is the only SES client
            # currently operating. The AWS_SES_AUTO_THROTTLE setting is a
            # factor to apply to the rate limit, with a default of 0.5 to stay
            # well below the actual SES throttle.
            # Set the setting to 0 or None to disable throttling.
            if self._throttle:
                global recent_send_times

                now = datetime.now()

                # Get and cache the current SES max-per-second rate limit
                # returned by the SES API.
                rate_limit = self.get_rate_limit()
                logger.debug("send_messages.throttle rate_limit='{}'".format(rate_limit))

                # Prune from recent_send_times anything more than a few seconds
                # ago. Even though SES reports a maximum per-second, the way
                # they enforce the limit may not be on a one-second window.
                # To be safe, we use a two-second window (but allow 2 times the
                # rate limit) and then also have a default rate limit factor of
                # 0.5 so that we really limit the one-second amount in two
                # seconds.
                window = 2.0  # seconds
                window_start = now - timedelta(seconds=window)
                new_send_times = []
                for time in recent_send_times:
                    if time > window_start:
                        new_send_times.append(time)
                recent_send_times = new_send_times

                # If the number of recent send times in the last 1/_throttle
                # seconds exceeds the rate limit, add a delay.
                # Since I'm not sure how Amazon determines at exactly what
                # point to throttle, better be safe than sorry and let in, say,
                # half of the allowed rate.
                if len(new_send_times) > rate_limit * window * self._throttle:
                    # Sleep the remainder of the window period.
                    delta = now - new_send_times[0]
                    total_seconds = (delta.microseconds + (delta.seconds +
                                     delta.days * 24 * 3600) * 10**6) / 10**6
                    delay = window - total_seconds
                    if delay > 0:
                        sleep(delay)

                recent_send_times.append(now)
                # end of throttling

            kwargs = dict(
                Source=source or message.from_email,
                Destinations=message.recipients(),
                # todo attachments?
                RawMessage={'Data': dkim_sign(message.message().as_string(),
                                              dkim_key=self.dkim_key,
                                              dkim_domain=self.dkim_domain,
                                              dkim_selector=self.dkim_selector,
                                              dkim_headers=self.dkim_headers)}
            )
            if self.ses_source_arn:
                kwargs['SourceArn'] = self.ses_source_arn
            if self.ses_from_arn:
                kwargs['FromArn'] = self.ses_from_arn
            if self.ses_return_path_arn:
                kwargs['ReturnPathArn'] = self.ses_return_path_arn

            try:
                response = self.connection.send_raw_email(**kwargs)
                message.extra_headers['status'] = 200
                message.extra_headers['message_id'] = response['MessageId']
                message.extra_headers['request_id'] = response['ResponseMetadata']['RequestId']
                num_sent += 1
                if 'X-SES-CONFIGURATION-SET' in message.extra_headers:
                    logger.debug(
                        "send_messages.sent from='{}' recipients='{}' message_id='{}' request_id='{}' "
                        "ses-configuration-set='{}'".format(
                            message.from_email,
                            ", ".join(message.recipients()),
                            message.extra_headers['message_id'],
                            message.extra_headers['request_id'],
                            message.extra_headers['X-SES-CONFIGURATION-SET']
                        ))
                else:
                    logger.debug("send_messages.sent from='{}' recipients='{}' message_id='{}' request_id='{}'".format(
                        message.from_email,
                        ", ".join(message.recipients()),
                        message.extra_headers['message_id'],
                        message.extra_headers['request_id']
                    ))

            except ResponseError as err:
                # Store failure information so to post process it if required
                error_keys = ['status', 'reason', 'body', 'request_id',
                              'error_code', 'error_message']
                for key in error_keys:
                    message.extra_headers[key] = getattr(err, key, None)
                if not self.fail_silently:
                    raise

        if new_conn_created:
            self.close()

        return num_sent

    def get_rate_limit(self):
        if self._access_key_id in cached_rate_limits:
            return cached_rate_limits[self._access_key_id]

        new_conn_created = self.open()
        if not self.connection:
            raise Exception(
                "No connection is available to check current SES rate limit.")
        try:
            quota_dict = self.connection.get_send_quota()
            max_per_second = quota_dict['MaxSendRate']
            ret = float(max_per_second)
            cached_rate_limits[self._access_key_id] = ret
            return ret
        finally:
            if new_conn_created:
                self.close()
