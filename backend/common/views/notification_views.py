"""REST endpoints for in-app notifications.

URL surface (mounted at /api/notifications/):
    GET  /: list, optional ?unread=true&limit=20&since=<iso>
    POST /<id>/read/: mark a single notification read
    POST /read-all/: mark all (or all-before-iso) read
    DELETE /<id>/: hard-delete a notification

Delivery is by polling: the client passes `?since=<iso>` on an interval and
receives whatever arrived after that timestamp. There was previously an SSE
stream at `/stream/`, removed 2026-08-03. It was the only async code in the
project, so it forced the whole deployment onto ASGI, where every in-flight
request takes its own database connection with no ceiling. That model caused
two production connection-exhaustion incidents. It was also silently broken:
its payload fetch ran on a connection with no `app.current_org` set, so under
a correctly configured non-superuser role every RLS policy matched zero rows
and the stream emitted keepalives and nothing else.

Polling costs far less than it appears to. At a 45s interval and a ~50ms
request, average concurrency is one request per ~900 open tabs, each borrowing
a pooled connection briefly and returning it.

Rules:
    - All queries filter by `recipient=request.profile`. RLS adds an org
      isolation safety net at the DB layer.
    - Mark-read is idempotent (re-marking does not move read_at backwards).
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Notification
from common.serializer import NotificationSerializer

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
    """GET /api/notifications/

    Also the delivery endpoint the client polls with ``?since=<iso>``.

    Note the two counts have different scopes, and the polling client depends
    on the difference:

    * ``count`` is the size of the *filtered* queryset, so under ``?since=``
      it is "how many arrived since", not the feed total.
    * ``unread_count`` is always computed over the recipient's whole feed,
      deliberately unfiltered, so a poll can refresh the bell badge without a
      second request.
    """

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
