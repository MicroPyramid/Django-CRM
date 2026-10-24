"""`POST /api/public/leads/<intake id>/`: a sender's post becomes a lead.

Anonymous by design, so no JWT, session or org. READ THE ORDER BELOW BEFORE
CHANGING IT:

1. The org comes from the intake id through the unscoped `PortalAccessToken`
   lookup (`leads/signals.py`), then the RLS context is set, and only then is
   the intake read, filtered on that org. An unknown id and a switched-off
   intake give the same 404.
2. The body is bounded (64 KB) and parsed before the key is checked, because
   two presets carry the key in it (Google Ads' `google_key`, and Tally's
   signature over the raw body).
3. The key: `Authorization: Bearer`, else the preset's own credential, else
   `?key=`. The first one present decides. Compared in constant time, against
   the current key and a replaced one until it expires.
4. A post without the key writes nothing: no delivery, no `last_error`, and it
   uses none of the webhook's quota, so a stranger holding the URL cannot
   crowd out or rate-limit the real sender. Those refusals are limited per
   client address instead (`RefusedPostThrottle`).
5. Only a caller holding the key learns that Leads is switched off, and only
   its posts count against the webhook's own limits.
6. A post is received under a lock on the intake row, after checking this
   webhook's deliveries for the same sender id, so a retry is a `duplicate`
   even when the first post merged into a lead that already had an id.

Every keyed outcome is logged as a `LeadIntakeEvent`. The reply never carries
more than the lead id. The key is never written to a log; `common.public_tokens`
cuts `?key=` from the access log, and `common.sentry_scrub` drops this route's
query, body and frame locals.
"""

import base64
import hashlib
import hmac
import json
import logging
import math
from urllib.parse import parse_qsl

from django.core.exceptions import RequestDataTooBig
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from common.models import PortalAccessToken
from common.modules import module_is_available
from common.org_time import activate_org_timezone
from common.portal_tokens import resolve_portal_org
from common.request_meta import client_ip
from common.tasks import set_rls_context
from leads.intake import IncomingLead, IntakeResult, receive_lead
from leads.intake_presets import preset_for, read_post
from leads.models import LeadIntake, LeadIntakeEvent

logger = logging.getLogger(__name__)

MAX_BODY = 64 * 1024
MAX_DEPTH = 32
MAX_FORM_FIELDS = 500
ERROR_MAX = 1000

NOT_FOUND = "Not found."
TOO_LARGE = "The body is larger than 64 KB."
WRONG_KEY = "Wrong key."
LEADS_OFF = "Leads are switched off for this organization."
NOTHING = "The post has no lead fields in it."
NOT_SAVED = "The lead could not be saved. Try again."
RATE_LIMITED = "rate limited"
TOO_MANY = "Too many posts. Try again later."
REFUSED_RATE = "60/min"
KEPT_RESULTS = ("created", "merged", "duplicate")


class _PerIntakeThrottle(SimpleRateThrottle):
    """Per intake, across every caller, so no number of addresses evades it."""

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": str(view.kwargs.get("intake_id")),
        }


class IntakeMinuteThrottle(_PerIntakeThrottle):
    scope = "lead_intake_minute"


class IntakeDayThrottle(_PerIntakeThrottle):
    scope = "lead_intake_day"


class RefusedPostThrottle(SimpleRateThrottle):
    """Refused posts (unknown webhook, wrong key, bad signature) per client
    address. A post with the key is never held back here: Google Ads, Tally
    and the like post for many accounts from shared addresses."""

    scope = "lead_intake_refused_ip"

    def get_rate(self):
        return self.THROTTLE_RATES.get(self.scope, REFUSED_RATE)

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": client_ip(request) or "unknown",
        }


class _AlwaysJSON(BaseContentNegotiation):
    """A sender's `Accept` header never turns a delivery into a 406."""

    def select_parser(self, request, parsers):
        return parsers[0] if parsers else None

    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type


class _TooDeep(Exception):
    pass


class LeadIntakePostView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)
    content_negotiation_class = _AlwaysJSON
    # Applied in the view: the webhook's own limits only once the key matched.
    throttle_classes = ()

    def post(self, request, intake_id):
        org_id = resolve_portal_org(intake_id, PortalAccessToken.LEAD_INTAKE)
        intake = None
        if org_id is not None:
            set_rls_context(org_id)
            intake = (
                LeadIntake.objects.filter(pk=intake_id, org_id=org_id, is_active=True)
                .select_related("org", "assignee")
                .first()
            )
        if intake is None:
            return self._refused(request, status.HTTP_404_NOT_FOUND, NOT_FOUND)
        activate_org_timezone(intake.org)
        preset = preset_for(intake.preset)

        raw, unreadable = _read_body(request)
        body, problem = None, None
        if raw is not None:
            body, problem = _parse(raw, request.META.get("CONTENT_TYPE", ""))
        if not _key_matches(request, intake, preset, raw, body):
            code, message = unreadable or (
                (status.HTTP_400_BAD_REQUEST, problem)
                if problem
                else (status.HTTP_401_UNAUTHORIZED, WRONG_KEY)
            )
            return self._refused(request, code, message, intake=intake)

        stored = _for_log(body, preset)
        wait = self._over_limit(request)
        if wait is not None:
            _log(intake, "rejected", error=RATE_LIMITED, payload=stored)
            return _too_many(wait)
        if unreadable is not None:
            return _refuse(intake, *unreadable)
        if problem:
            return _refuse(intake, status.HTTP_400_BAD_REQUEST, problem)
        if not module_is_available(intake.org, "leads"):
            return _refuse(intake, status.HTTP_403_FORBIDDEN, LEADS_OFF, stored)

        reading = read_post(intake, body)
        if reading.is_test:
            _log(intake, "test", external_id=reading.external_id, payload=stored)
            return _answer(status.HTTP_200_OK, result="test")
        if reading.errors:
            errors = {
                name: [str(m) for m in messages]
                for name, messages in reading.errors.items()
            }
            described = "; ".join(f"{k}: {' '.join(v)}" for k, v in errors.items())
            _log(
                intake,
                "rejected",
                external_id=reading.external_id,
                error=described,
                payload=stored,
            )
            return _answer(
                status.HTTP_400_BAD_REQUEST,
                result="rejected",
                detail="Some values in the post could not be saved.",
                errors=errors,
            )
        if not (reading.values or reading.custom_fields or reading.enquiry_text):
            return _refuse(intake, status.HTTP_400_BAD_REQUEST, NOTHING, stored)

        incoming = IncomingLead(
            values=reading.values,
            custom_fields=reading.custom_fields,
            source=intake.default_source,
            source_detail=intake.source_detail,
            source_ref=reading.source_ref,
            external_source=f"intake:{intake.id}",
            external_id=reading.external_id,
            tags=tuple(intake.tags.all()),
            assignee=intake.assignee,
            enquiry_text=reading.enquiry_text,
            channel_label=f"webhook {intake.name}",
            occurred_at=reading.occurred_at,
        )
        try:
            with transaction.atomic():
                list(
                    LeadIntake.objects.select_for_update()
                    .filter(pk=intake.pk, org_id=intake.org_id)
                    .values_list("pk", flat=True)
                )
                result = _seen(intake, reading.external_id) or receive_lead(
                    intake.org, incoming
                )
                _log(
                    intake,
                    result.result,
                    lead=result.lead,
                    external_id=reading.external_id,
                    payload=stored,
                )
        except Exception:
            # Rolled back whole; logged so the delivery is not lost without a
            # trace, and a 5xx so the sender retries.
            logger.exception("Lead webhook %s could not save a delivery", intake.id)
            _log(
                intake,
                "rejected",
                external_id=reading.external_id,
                error=NOT_SAVED,
                payload=stored,
            )
            return _answer(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=NOT_SAVED)

        code = status.HTTP_201_CREATED if result.result == "created" else 200
        return _answer(code, result=result.result, lead=str(result.lead.id))

    def _refused(self, request, code, message, intake=None):
        """A post without the key: counted against its address, logged for
        an existing webhook without the body or the key, nothing written."""
        throttle = RefusedPostThrottle()
        if not throttle.allow_request(request, self):
            return _too_many(throttle.wait())
        if intake is not None:
            logger.warning("Lead webhook %s refused a post: %s", intake.id, message)
        return _answer(code, detail=message)

    def _over_limit(self, request):
        """Seconds to wait when this webhook is over a limit, else None. The
        day bucket only counts posts the minute bucket let through."""
        for throttle in (IntakeMinuteThrottle(), IntakeDayThrottle()):
            if not throttle.allow_request(request, self):
                return throttle.wait() or 0
        return None


def _answer(code, **body):
    return Response(body, status=code)


def _too_many(wait):
    response = _answer(status.HTTP_429_TOO_MANY_REQUESTS, detail=TOO_MANY)
    if wait is not None:
        response["Retry-After"] = str(math.ceil(wait))
    return response


def _for_log(body, preset):
    if body is None or not (preset.key_field and preset.key_field in body):
        return body
    return {**body, preset.key_field: "[Filtered]"}


def _seen(intake, external_id):
    """This webhook already received the sender's id and it reached a lead."""
    if not external_id:
        return None
    event = (
        LeadIntakeEvent.objects.filter(
            org_id=intake.org_id,
            intake=intake,
            external_id=external_id,
            result__in=KEPT_RESULTS,
            lead__isnull=False,
        )
        .select_related("lead")
        .order_by("-received_at")
        .first()
    )
    return IntakeResult("duplicate", event.lead) if event is not None else None


def _refuse(intake, code, message, payload=None):
    _log(intake, "rejected", error=message, payload=payload)
    return _answer(code, detail=message)


def _log(intake, result, *, lead=None, external_id="", error="", payload=None):
    """Record one delivery, move the intake's stamps, and drop its old events."""
    now = timezone.now()
    LeadIntakeEvent.objects.create(
        org_id=intake.org_id,
        intake=intake,
        received_at=now,
        result=result,
        lead=lead,
        external_id=external_id[:255],
        error=error[:ERROR_MAX],
        payload=payload,
    )
    stamps = (
        {"last_error": error[:ERROR_MAX]}
        if result == "rejected"
        else {"last_error": "", "last_received_at": now}
    )
    LeadIntake.objects.filter(pk=intake.pk, org_id=intake.org_id).update(**stamps)
    intake.drop_old_events()


def _read_body(request):
    try:
        declared = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return None, (status.HTTP_400_BAD_REQUEST, "Content-Length is not a number.")
    if declared > MAX_BODY:
        return None, (status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, TOO_LARGE)
    try:
        raw = request.body
    except RequestDataTooBig:
        return None, (status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, TOO_LARGE)
    if len(raw) > MAX_BODY:
        return None, (status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, TOO_LARGE)
    return raw, None


def _parse(raw, content_type):
    """The body as a dict of clean strings, or ``(None, why not)``."""
    media = content_type.split(";", 1)[0].strip().lower()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, "The body is not UTF-8."
    if media == "application/x-www-form-urlencoded":
        try:
            pairs = parse_qsl(
                text, keep_blank_values=True, max_num_fields=MAX_FORM_FIELDS
            )
        except ValueError:
            return None, f"Send at most {MAX_FORM_FIELDS} fields."
        body = {}
        for key, value in pairs:
            body.setdefault(key, []).append(value)
        body = {k: v[0] if len(v) == 1 else v for k, v in body.items()}
    elif media == "application/json" or media.endswith("+json") or not media:
        try:
            body = json.loads(text, parse_constant=_refuse_constant)
        except (ValueError, RecursionError):
            return None, "The body is not valid JSON."
    else:
        return None, "Send the body as JSON or form-encoded."
    if not isinstance(body, dict):
        return None, "The body must be a JSON object."
    try:
        return _clean(body, 0), None
    except _TooDeep:
        return None, "The body is nested too deeply."


def _refuse_constant(name):
    raise ValueError(f"{name} is not JSON")


def _clean(node, depth):
    """NUL characters and lone surrogates out of every string: the database
    refuses both, and they would turn a delivery into a 500."""
    if depth > MAX_DEPTH:
        raise _TooDeep
    if isinstance(node, str):
        return node.replace("\x00", "").encode("utf-8", "replace").decode("utf-8")
    if isinstance(node, dict):
        return {_clean(k, depth): _clean(v, depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        return [_clean(v, depth + 1) for v in node]
    return node


def _key_matches(request, intake, preset, raw, body):
    keys = [intake.key]
    expires = intake.previous_key_expires_at
    if intake.previous_key and expires is not None and expires > timezone.now():
        keys.append(intake.previous_key)
    keys = [key.encode() for key in keys if key]

    scheme, _, secret = request.META.get("HTTP_AUTHORIZATION", "").partition(" ")
    if scheme.lower() == "bearer" and secret.strip():
        return _matches(secret.strip(), keys)
    if preset.signature_header:
        signature = request.headers.get(preset.signature_header, "").strip()
        if signature:
            return raw is not None and any(
                hmac.compare_digest(
                    signature.encode(),
                    base64.b64encode(hmac.new(key, raw, hashlib.sha256).digest()),
                )
                for key in keys
            )
    if preset.key_field and isinstance(body, dict) and preset.key_field in body:
        secret = body[preset.key_field]
        return isinstance(secret, str) and _matches(secret, keys)
    secret = request.GET.get("key", "")
    return bool(secret) and _matches(secret, keys)


def _matches(secret, keys):
    presented = secret.encode()
    return any(hmac.compare_digest(presented, key) for key in keys)
