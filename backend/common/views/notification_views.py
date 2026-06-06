"""REST endpoints for in-app notifications.

URL surface (mounted at /api/notifications/):
    GET  /                  — list, optional ?unread=true&limit=20&since=<iso>
    GET  /stream/           — SSE event stream (one event per new notification)
    POST /<id>/read/        — mark a single notification read
    POST /read-all/         — mark all (or all-before-iso) read
    DELETE /<id>/           — hard-delete a notification

Rules:
    - All queries filter by `recipient=request.profile`. RLS adds an org
      isolation safety net at the DB layer.
    - Mark-read is idempotent (re-marking does not move read_at backwards).
"""

import asyncio
import json
import logging
import time

from asgiref.sync import sync_to_async
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from common import notifications as notif_mod
from common.models import Notification
from common.serializer import NotificationSerializer

logger = logging.getLogger(__name__)

KEEPALIVE_SECONDS = 15

# Upper bound on a single SSE connection's lifetime. The browser's EventSource
# transparently reconnects when the server closes the stream, so capping this
# is invisible to the user but critical for the server: under ASGI the *entire*
# stream runs inside one request (one `ThreadSensitiveContext`), so an
# unbounded `while True` stream pins a worker thread — and any DB/redis
# connection bound to it — for as long as the tab stays open (hours). Left
# unbounded this is what slowly exhausts a shared Postgres cluster and leaves
# workers undrainable on deploy. 5 minutes bounds the leak window and lets
# workers recycle.
MAX_STREAM_SECONDS = 300

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _user_qs(request):
    return Notification.objects.filter(recipient=request.profile)


def _parse_int(raw, default, *, lo=1, hi=MAX_LIMIT):
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


class NotificationListView(APIView):
    """GET /api/notifications/"""

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        params = request.query_params
        qs = _user_qs(request)
        unread_only = params.get("unread", "").lower() == "true"
        if unread_only:
            qs = qs.filter(read_at__isnull=True)
        if params.get("since"):
            since_dt = parse_datetime(params.get("since"))
            if since_dt is not None:
                qs = qs.filter(created_at__gt=since_dt)

        total = qs.count()
        unread_count = _user_qs(request).filter(read_at__isnull=True).count()

        limit = _parse_int(params.get("limit"), DEFAULT_LIMIT)
        results = NotificationSerializer(qs[:limit], many=True).data

        return Response(
            {
                "count": total,
                "unread_count": unread_count,
                "results": results,
            }
        )


class NotificationReadView(APIView):
    """POST /api/notifications/<id>/read/"""

    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        notif = get_object_or_404(_user_qs(request), pk=pk)
        if notif.read_at is None:
            notif.read_at = timezone.now()
            notif.save(update_fields=["read_at", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationReadAllView(APIView):
    """POST /api/notifications/read-all/   body: {"before": "<iso>"}"""

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        before = request.data.get("before") if isinstance(request.data, dict) else None
        cutoff = parse_datetime(before) if before else timezone.now()
        if cutoff is None:
            cutoff = timezone.now()
        _user_qs(request).filter(read_at__isnull=True, created_at__lte=cutoff).update(
            read_at=timezone.now()
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationDetailView(APIView):
    """DELETE /api/notifications/<id>/"""

    permission_classes = (IsAuthenticated,)

    def delete(self, request, pk, *args, **kwargs):
        notif = get_object_or_404(_user_qs(request), pk=pk)
        notif.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- SSE stream ---------------------------------------------------------


def _format_sse(event: str, data: dict) -> bytes:
    """Encode one Server-Sent Events frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


def _format_keepalive() -> bytes:
    # Comment lines (starting with ':') are silently ignored by the EventSource
    # client but defeat reverse-proxy buffering on idle connections.
    return b": keepalive\n\n"


async def _aget_serialized(notif_id, recipient_id):
    """Fetch a notification by id, scoped to recipient. Returns dict or None."""
    @sync_to_async
    def fetch():
        from django.db import connection

        try:
            notif = Notification.objects.filter(
                pk=notif_id, recipient_id=recipient_id
            ).first()
            if notif is None:
                return None
            return NotificationSerializer(notif).data
        finally:
            # This runs in asgiref's shared thread-sensitive executor, outside
            # Django's request/response cycle — so `close_old_connections`
            # never fires for it. Without this explicit close the connection
            # dangles open (the SSE tests need TransactionTestCase precisely
            # because of it). Close it so each fetch reclaims its connection.
            connection.close()

    return await fetch()


async def _aclose_redis(obj):
    """Close a redis.asyncio client/pubsub across versions (aclose vs close)."""
    if obj is None:
        return
    closer = getattr(obj, "aclose", None) or getattr(obj, "close", None)
    if closer is None:
        return
    try:
        result = closer()
        if asyncio.iscoroutine(result):
            await result
    except Exception:  # pragma: no cover - best effort
        pass


async def _open_pubsub(channel: str):
    """Open a redis.asyncio pubsub subscribed to ``channel``.

    Returns ``(client, pubsub)``. Both are ``None`` if Redis is unreachable;
    the stream then runs in keepalive-only mode (the frontend's polling-since
    path provides backfill). The caller owns closing BOTH the pubsub and the
    underlying client connection pool — closing only the pubsub leaks the
    client's pooled connections, one per dropped SSE stream.
    """
    try:
        import redis.asyncio as aioredis  # type: ignore
    except ImportError:  # pragma: no cover
        return None, None
    from django.conf import settings

    url = getattr(settings, "CELERY_BROKER_URL", None) or "redis://localhost:6379/0"
    client = None
    try:
        client = aioredis.from_url(url)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        return client, pubsub
    except Exception as exc:
        logger.warning("SSE redis subscribe failed (%s); keepalive-only mode", exc)
        await _aclose_redis(client)
        return None, None


async def _stream_events(channel: str, recipient_id, *, pubsub=None):
    """Async generator yielding SSE-formatted bytes for the recipient's channel.

    Pass ``pubsub`` to inject a stub for tests. When omitted the generator
    opens its own redis.asyncio pubsub via :func:`_open_pubsub`.
    """
    owns_pubsub = pubsub is None
    client = None
    if owns_pubsub:
        client, pubsub = await _open_pubsub(channel)
    deadline = time.monotonic() + MAX_STREAM_SECONDS
    try:
        # Initial comment so the client confirms the stream opened.
        yield _format_keepalive()
        while True:
            # Bounded lifetime: end the stream so the worker thread and its
            # DB/redis connections are released. EventSource reconnects.
            if time.monotonic() >= deadline:
                return
            if pubsub is None:
                await asyncio.sleep(KEEPALIVE_SECONDS)
                yield _format_keepalive()
                continue
            try:
                msg = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=KEEPALIVE_SECONDS,
                )
            except asyncio.TimeoutError:
                yield _format_keepalive()
                continue
            if msg is None:
                await asyncio.sleep(0.5)
                continue
            data = msg.get("data")
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            payload = await _aget_serialized(data, recipient_id)
            if payload is None:
                continue
            yield _format_sse("notification", payload)
    finally:
        if owns_pubsub:
            if pubsub is not None:
                try:
                    await pubsub.unsubscribe(channel)
                except Exception:  # pragma: no cover - best effort
                    pass
                await _aclose_redis(pubsub)
            # Close the underlying client pool too — not just the pubsub.
            await _aclose_redis(client)


def _drive_async_gen(agen):
    """Yield from an async generator using a dedicated event loop.

    DRF's APIView dispatch is sync, so we can't expose an `async def` handler
    directly (Django would mark the view async via `view_is_async`, then DRF's
    sync dispatch returns a Response that the async wrapper tries to await).
    StreamingHttpResponse accepts a sync iterable, so we bridge here.
    """
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                yield loop.run_until_complete(agen.__anext__())
            except StopAsyncIteration:
                return
    finally:
        try:
            loop.run_until_complete(agen.aclose())
        finally:
            loop.close()


class _EventStreamRenderer(BaseRenderer):
    """Advertises text/event-stream for DRF content negotiation.

    Never actually invoked — the view returns a StreamingHttpResponse directly.
    Without this, an EventSource sending `Accept: text/event-stream` is
    rejected by DRF's content negotiation with HTTP 406 (no matching renderer).
    """

    media_type = "text/event-stream"
    format = "sse"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return b""


class NotificationStreamView(APIView):
    """GET /api/notifications/stream/

    Long-lived Server-Sent Events response. Requires an ASGI server in
    production — under WSGI this view ties up one worker per connected user.
    """

    permission_classes = (IsAuthenticated,)
    renderer_classes = (_EventStreamRenderer,)

    def get(self, request, *args, **kwargs):
        org_id = request.profile.org_id
        profile_id = request.profile.id
        channel = notif_mod.channel_for(org_id, profile_id)

        # Release THIS request thread's DB connection before streaming begins.
        # Under ASGI the entire stream runs inside one request's
        # ThreadSensitiveContext, so the connection opened by auth/middleware
        # would otherwise stay checked out for the full (possibly hours-long)
        # stream — one leaked Postgres connection per open browser tab, which
        # is what exhausts the shared cluster. The stream's own reads go
        # through a separate executor (see `_aget_serialized`) and close
        # themselves, so dropping this one is safe.
        from django.db import connection

        connection.close()

        response = StreamingHttpResponse(
            _drive_async_gen(_stream_events(channel, profile_id)),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"  # disable nginx buffering
        return response
