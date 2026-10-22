import logging

from automation import capture, engine

logger = logging.getLogger(__name__)


class AutomationMiddleware:
    """Hand the changes a request captured to the rule engine, once its view
    has returned. See `automation.capture` for what is captured.

    Must sit after `webhooks.middleware.WebhookEventsMiddleware`, so this
    runs first on the way out and the webhook flush sees a rule's own writes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            changes = capture.flush(request)
            if changes:
                engine.process(changes)
        except Exception:
            # The view's writes are already saved, so the reply still goes
            # out. Logged without the records' data.
            logger.exception("Automation rules could not run for a request")
        return response
