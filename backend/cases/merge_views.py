"""Case merge endpoint.

Merges a duplicate ("source") Case into a primary ("target") Case in a single
atomic transaction. Re-points comments, attachments, and inbound email
messages from source → target; sets `source.merged_into = target` and stamps
status=Duplicate / closed_on=today; emits MERGED on the source and
MERGE_TARGET on the target.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Case, EmailMessage
from cases.serializer import CaseSerializer
from cases.signals import _create_activity
from common.models import Attachments, Comment
from common.permissions import HasOrgContext


def _can_merge(profile, source: Case, target: Case) -> bool:
    """Admin OR the creator of BOTH cases."""
    if profile.is_admin or profile.role == "ADMIN":
        return True
    user = profile.user
    return source.created_by_id == user.id and target.created_by_id == user.id


class CaseMergeView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        operation_id="cases_merge",
        tags=["Cases"],
        responses={
            200: inline_serializer(
                name="CaseMergeResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "already_merged": serializers.BooleanField(required=False),
                    "target_case": CaseSerializer(),
                    "source_case_id": serializers.CharField(),
                    "redirected_url": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request, pk: str, into_id: str, format=None):
        org = request.profile.org

        if pk == into_id:
            return Response(
                {"error": True, "errors": "Cannot merge a case into itself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lock both rows in a deterministic order to avoid deadlocks under
        # concurrent merges that touch overlapping pairs.
        ordered_ids = sorted([pk, into_id])
        with transaction.atomic():
            locked = list(
                Case.objects.select_for_update()
                .filter(id__in=ordered_ids, org=org)
            )
            by_id = {str(c.id): c for c in locked}
            source = by_id.get(str(pk))
            target = by_id.get(str(into_id))

            if not source or not target:
                return Response(
                    {"error": True, "errors": "Case not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not _can_merge(request.profile, source, target):
                return Response(
                    {
                        "error": True,
                        "errors": (
                            "You must be an admin, or the creator of both "
                            "cases, to merge them."
                        ),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Idempotency: source already merged into the same target → no-op.
            if source.merged_into_id is not None:
                if str(source.merged_into_id) == str(target.id):
                    return Response(
                        {
                            "error": False,
                            "message": "Cases already merged.",
                            "already_merged": True,
                            "target_case": CaseSerializer(target).data,
                            "source_case_id": str(source.id),
                            "redirected_url": f"/cases/{target.id}",
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {
                        "error": True,
                        "errors": "Source case is already merged into a different case.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Reject chains: target itself is a duplicate of someone else.
            if target.merged_into_id is not None:
                return Response(
                    {
                        "error": True,
                        "errors": "Target case has already been merged elsewhere.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            case_ct = ContentType.objects.get_for_model(Case)

            comments_moved = Comment.objects.filter(
                content_type=case_ct, object_id=source.id, org=org
            ).update(object_id=target.id)
            attachments_moved = Attachments.objects.filter(
                content_type=case_ct, object_id=source.id, org=org
            ).update(object_id=target.id)
            emails_moved = EmailMessage.objects.filter(
                case=source, org=org
            ).update(case=target)

            # Inherit the duplicate's thread keys onto the primary so future
            # inbound emails to the old thread land on the primary.
            target_alts = list(target.alt_thread_ids or [])
            source_alts = list(source.alt_thread_ids or [])
            inherited = source_alts + (
                [source.external_thread_id] if source.external_thread_id else []
            )
            for tid in inherited:
                if tid and tid not in target_alts:
                    target_alts.append(tid)
            target.alt_thread_ids = target_alts
            target.save(update_fields=["alt_thread_ids", "updated_at"])

            now = timezone.now()
            source.merged_into = target
            source.merged_at = now
            source.merged_by = request.profile
            source.status = "Duplicate"
            source.closed_on = now.date()
            source.save(
                update_fields=[
                    "merged_into",
                    "merged_at",
                    "merged_by",
                    "status",
                    "closed_on",
                    "updated_at",
                ]
            )

            _create_activity(
                target,
                "MERGE_TARGET",
                metadata={
                    "source_id": str(source.id),
                    "comments_moved": comments_moved,
                    "attachments_moved": attachments_moved,
                    "emails_moved": emails_moved,
                },
                actor=request.profile,
            )
            _create_activity(
                source,
                "MERGED",
                metadata={"merged_into": str(target.id)},
                actor=request.profile,
            )

        return Response(
            {
                "error": False,
                "message": "Cases merged",
                "target_case": CaseSerializer(target).data,
                "source_case_id": str(source.id),
                "redirected_url": f"/cases/{target.id}",
            },
            status=status.HTTP_200_OK,
        )
