"""Tests for the Server-Sent Events notification stream.

Covers:
    - Pure-function helpers (`_format_sse`, `_format_keepalive`).
    - The async generator `_stream_events` with an injected stub pubsub
      (no real Redis required).
    - The auth gate on the view.
"""

import asyncio
import json

from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from common.models import Notification, Org, Profile, User
from common.views.notification_views import (
    _format_keepalive,
    _format_sse,
    _stream_events,
)


class TestFormatHelpers:
    def test_format_sse_event_shape(self):
        out = _format_sse("notification", {"id": "abc", "verb": "v"})
        assert out.startswith(b"event: notification\n")
        assert b"data: " in out
        assert out.endswith(b"\n\n")
        data_line = [l for l in out.split(b"\n") if l.startswith(b"data: ")][0]
        payload = json.loads(data_line[len(b"data: "):])
        assert payload == {"id": "abc", "verb": "v"}

    def test_format_keepalive_is_comment(self):
        # SSE comment lines start with ':'
        assert _format_keepalive() == b": keepalive\n\n"


class _StubPubSub:
    """Duck-typed redis.asyncio pubsub.

    Pulls messages from a list; once exhausted, returns None forever.
    """

    def __init__(self, messages=None):
        self._messages = list(messages or [])
        self.subscribed = []
        self.unsubscribed = []
        self.closed = False

    async def subscribe(self, channel):
        self.subscribed.append(channel)

    async def unsubscribe(self, channel):
        self.unsubscribed.append(channel)

    async def close(self):
        self.closed = True

    async def get_message(self, ignore_subscribe_messages=False):
        if self._messages:
            return self._messages.pop(0)
        return None


class TestStreamEvents(TransactionTestCase):
    """Uses TransactionTestCase because the SSE generator's `sync_to_async`
    DB hit opens a separate SQLite connection — incompatible with the
    transaction-wrapped TestCase isolation."""

    def setUp(self):
        self.org = Org.objects.create(name="O")
        self.user = User.objects.create_user(email="u@test.com", password="x")
        self.profile = Profile.objects.create(
            user=self.user, org=self.org, role="USER", is_active=True
        )
        self.other_user = User.objects.create_user(email="x@test.com", password="x")
        self.other_profile = Profile.objects.create(
            user=self.other_user, org=self.org, role="USER", is_active=True
        )

    def test_first_frame_is_keepalive(self):
        async def runner():
            pubsub = _StubPubSub()
            gen = _stream_events("notif:o:p", recipient_id=self.profile.id, pubsub=pubsub)
            first = await asyncio.wait_for(gen.__anext__(), timeout=1)
            await gen.aclose()
            return first

        first = asyncio.run(runner())
        assert first == b": keepalive\n\n"

    def test_emits_notification_for_pubsub_message(self):
        notif = Notification.objects.create(
            org=self.org,
            recipient=self.profile,
            verb="case.commented",
            data={"comment_excerpt": "hi"},
            link="/cases/abc",
        )

        async def runner():
            pubsub = _StubPubSub([{"data": str(notif.id).encode("utf-8")}])
            gen = _stream_events(
                "notif:o:p", recipient_id=self.profile.id, pubsub=pubsub
            )
            first = await asyncio.wait_for(gen.__anext__(), timeout=1)
            second = await asyncio.wait_for(gen.__anext__(), timeout=2)
            await gen.aclose()
            return first, second

        first, second = asyncio.run(runner())
        assert first == b": keepalive\n\n"
        assert second.startswith(b"event: notification\n")
        data_line = [l for l in second.split(b"\n") if l.startswith(b"data: ")][0]
        payload = json.loads(data_line[len(b"data: "):])
        assert payload["id"] == str(notif.id)
        assert payload["verb"] == "case.commented"
        assert payload["link"] == "/cases/abc"
        assert payload["data"] == {"comment_excerpt": "hi"}

    def test_drops_message_for_other_recipient(self):
        n_other = Notification.objects.create(
            org=self.org, recipient=self.other_profile, verb="other"
        )
        n_mine = Notification.objects.create(
            org=self.org, recipient=self.profile, verb="mine"
        )

        async def runner():
            pubsub = _StubPubSub(
                [
                    {"data": str(n_other.id).encode("utf-8")},
                    {"data": str(n_mine.id).encode("utf-8")},
                ]
            )
            gen = _stream_events(
                "notif:o:p", recipient_id=self.profile.id, pubsub=pubsub
            )
            await asyncio.wait_for(gen.__anext__(), timeout=1)  # discard initial keepalive
            second = await asyncio.wait_for(gen.__anext__(), timeout=2)
            await gen.aclose()
            return second

        second = asyncio.run(runner())
        assert second.startswith(b"event: notification\n")
        data_line = [l for l in second.split(b"\n") if l.startswith(b"data: ")][0]
        payload = json.loads(data_line[len(b"data: "):])
        # Should be MINE, never the other recipient's row
        assert payload["id"] == str(n_mine.id)
        assert payload["verb"] == "mine"


class TestStreamAuth(TestCase):
    def test_unauthenticated_rejected(self):
        anon = APIClient()
        r = anon.get("/api/notifications/stream/")
        try:
            assert r.status_code in (401, 403)
        finally:
            close = getattr(r, "close", None)
            if close:
                close()
