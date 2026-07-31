"""Inbound email webhook + admin mailbox CRUD endpoints.

The webhook is intentionally public (no auth). All trust is anchored on the
SNS signature verification: an attacker who can't sign a message with the AWS
SNS signing cert can't get past `verify_sns_message`.
"""

from __future__ import annotations

import json
import logging
import secrets
from datetime import timedelta

from django.db.models import Count, Max
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.inbound.parser import parse_raw_email
from cases.inbound.pipeline import ingest
from cases.inbound.sns import (
    SNSVerificationError,
    confirm_subscription,
    verify_sns_message,
)
from cases.models import EmailMessage, InboundMailbox
from cases.serializer import InboundMailboxSerializer
from common.permissions import HasOrgContext
from common.tasks import set_rls_context

logger = logging.getLogger(__name__)

# Window the mailbox page reports ticket counts over.
MAILBOX_WINDOW_DAYS = 30


def _is_admin(profile):
    return profile.role == "ADMIN" or getattr(profile, "is_admin", False)


def _mailbox_analytics(org):
    """Per-mailbox ticket counts + last-received timestamp, plus an org total.

    Both come from the ``EmailMessage.mailbox`` FK (set at ingest since the
    migration): a message records exactly which inbound address it arrived
    through, so these are attributed, not guessed.

    - ``cases_last_30d`` per mailbox = distinct cases *created* in the last 30
      days that have an inbound message through that mailbox (a reply arriving
      at the address for an older case is not a new ticket, so we anchor on the
      case's ``created_at``).
    - ``last_received_at`` per mailbox = the newest inbound message's
      ``received_at`` (any message, including dropped ones — the address still
      received mail).
    - org ``cases_last_30d`` = distinct such cases across all mailboxes (not a
      sum, so a case cross-posted to two addresses is not double counted).

    All scoped to ``org`` explicitly (RLS is inert in dev/test).
    """
    cutoff = timezone.now() - timedelta(days=MAILBOX_WINDOW_DAYS)
    inbound = EmailMessage.objects.filter(
        org=org, direction="inbound", mailbox__isnull=False
    )
    created = (
        inbound.filter(case__isnull=False, case__created_at__gte=cutoff)
        .values("mailbox_id")
        .annotate(n=Count("case", distinct=True))
    )
    cases_by_mailbox = {str(row["mailbox_id"]): row["n"] for row in created}
    last = inbound.values("mailbox_id").annotate(last=Max("received_at"))
    last_by_mailbox = {str(row["mailbox_id"]): row["last"] for row in last}
    total_cases = (
        inbound.filter(case__isnull=False, case__created_at__gte=cutoff)
        .values("case")
        .distinct()
        .count()
    )
    return cases_by_mailbox, last_by_mailbox, total_cases


def _admin_required():
    return Response(
        {"error": True, "errors": "Admin access required"},
        status=status.HTTP_403_FORBIDDEN,
    )


class InboundMailboxWebhookView(APIView):
    """Public endpoint where AWS SNS POSTs for one configured mailbox.

    URL: `/api/cases/inbound/<mailbox_id>/`. The mailbox lookup also acts as
    the org boundary — the URL embeds the per-mailbox UUID so the webhook
    can't be confused for one belonging to a different tenant.
    """

    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["InboundEmail"],
        request=inline_serializer(
            name="SNSInboundPayload",
            fields={
                "Type": serializers.CharField(),
                "Message": serializers.CharField(),
                "Signature": serializers.CharField(),
                "SigningCertURL": serializers.CharField(),
            },
        ),
        responses={
            200: inline_serializer(
                name="InboundWebhookResponse",
                fields={
                    "ok": serializers.BooleanField(),
                    "case_id": serializers.CharField(allow_null=True, required=False),
                    "dropped": serializers.BooleanField(required=False),
                    "reason": serializers.CharField(required=False),
                },
            )
        },
    )
    def post(self, request, mailbox_id, *args, **kwargs):
        mailbox = (
            InboundMailbox.objects.filter(pk=mailbox_id, is_active=True)
            .select_related("org")
            .first()
        )
        if mailbox is None:
            # Don't leak which UUIDs exist; return a generic 404.
            return Response(
                {"error": True, "errors": "Mailbox not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # The webhook bypasses RLSContextMiddleware, so set it manually before
        # any ORM read/write touches an org-scoped table.
        set_rls_context(mailbox.org_id)

        if mailbox.provider != "ses":
            # Other providers wired into the same URL space land here.
            return Response(
                {
                    "error": True,
                    "errors": f"Provider {mailbox.provider!r} not yet supported",
                },
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        # SNS posts the JSON body in `request.body` — DRF may have parsed it.
        try:
            payload = (
                request.data
                if isinstance(request.data, dict)
                else json.loads(request.body or b"{}")
            )
        except (ValueError, TypeError):
            return Response(
                {"error": True, "errors": "Body is not valid JSON"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            verify_sns_message(payload)
        except SNSVerificationError as exc:
            logger.warning(
                "SNS verification failed for mailbox=%s: %s", mailbox.id, exc
            )
            return Response(
                {"error": True, "errors": "Signature verification failed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        msg_type = payload.get("Type")
        if msg_type == "SubscriptionConfirmation":
            try:
                confirm_subscription(payload)
            except Exception:
                logger.exception("SNS subscription confirmation failed")
                return Response(
                    {"error": True, "errors": "SubscribeURL fetch failed"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            return Response({"ok": True, "subscribed": True})

        if msg_type == "UnsubscribeConfirmation":  # pragma: no cover — informational
            logger.info("SNS unsubscribe for mailbox=%s", mailbox.id)
            return Response({"ok": True, "unsubscribed": True})

        if msg_type != "Notification":
            return Response(
                {"error": True, "errors": f"Unsupported SNS Type: {msg_type!r}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # SES with "SNS Notification with full content" puts the raw RFC-5322
        # email in payload.Message as a plain string. Older SES configurations
        # send a JSON envelope (`{"notificationType":"Received","content":"..."}`);
        # peel that off if we see it.
        raw_message = payload.get("Message", "") or ""
        try:
            envelope = json.loads(raw_message)
            if isinstance(envelope, dict) and "content" in envelope:
                raw_message = envelope.get("content") or ""
        except (ValueError, TypeError):
            pass

        if not raw_message:
            return Response(
                {"error": True, "errors": "SNS Message body is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed = parse_raw_email(raw_message)
        result = ingest(parsed, mailbox)

        return Response(
            {
                "ok": True,
                "case_id": str(result.case.id) if result.case else None,
                "dropped": result.dropped,
                "reason": result.drop_reason,
                "created_case": result.created_case,
            },
            status=status.HTTP_200_OK,
        )


class InboundMailboxListCreateView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["InboundEmail"], responses={200: InboundMailboxSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        org = request.profile.org
        qs = InboundMailbox.objects.filter(org=org).order_by("address")
        mailboxes = InboundMailboxSerializer(
            qs, many=True, context={"request": request}
        ).data
        cases_by, last_by, total_cases = _mailbox_analytics(org)
        active = 0
        for mbx in mailboxes:
            mid = str(mbx["id"])
            mbx["cases_last_30d"] = cases_by.get(mid, 0)
            received = last_by.get(mid)
            mbx["last_received_at"] = received.isoformat() if received else None
            if mbx["is_active"]:
                active += 1
        totals = {
            "count": len(mailboxes),
            "active": active,
            "cases_last_30d": total_cases,
        }
        return Response({"mailboxes": mailboxes, "totals": totals})

    @extend_schema(
        tags=["InboundEmail"],
        request=InboundMailboxSerializer,
        responses={201: InboundMailboxSerializer},
    )
    def post(self, request, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        data = dict(request.data)
        # Auto-generate a webhook secret on create when the admin didn't paste one.
        if not data.get("webhook_secret"):
            data["webhook_secret"] = secrets.token_urlsafe(32)
        serializer = InboundMailboxSerializer(
            data=data, context={"org": org, "request": request}
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(org=org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InboundMailboxDetailView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get_object(self, pk, org):
        return InboundMailbox.objects.filter(pk=pk, org=org).first()

    @extend_schema(tags=["InboundEmail"], responses={200: InboundMailboxSerializer})
    def get(self, request, pk, *args, **kwargs):
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Mailbox not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            InboundMailboxSerializer(obj, context={"request": request}).data
        )

    @extend_schema(
        tags=["InboundEmail"],
        request=InboundMailboxSerializer,
        responses={200: InboundMailboxSerializer},
    )
    def put(self, request, pk, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        obj = self._get_object(pk, org)
        if not obj:
            return Response(
                {"error": True, "errors": "Mailbox not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = InboundMailboxSerializer(
            obj,
            data=request.data,
            partial=True,
            context={"org": org, "request": request},
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["InboundEmail"],
        responses={
            200: inline_serializer(
                name="MailboxDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Mailbox not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        obj.delete()
        return Response({"error": False, "message": "Mailbox deleted"})
