"""Bulk update / bulk delete endpoints for the Cases module."""

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Case
from common.models import Activity, Profile, Tags
from common.permissions import HasOrgContext

ALLOWED_FIELDS = {"status", "priority", "case_type", "closed_on"}
ALLOWED_M2M = {"assigned_to": Profile, "tags": Tags}


class BulkUpdateCasesView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def post(self, request):
        ids = request.data.get("ids") or []
        fields = request.data.get("fields") or {}
        if not ids:
            return Response(
                {"error": True, "errors": "ids required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unknown = set(fields) - ALLOWED_FIELDS - set(ALLOWED_M2M)
        if unknown:
            return Response(
                {"error": True, "errors": f"Unsupported fields: {sorted(unknown)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scalar_updates = {k: v for k, v in fields.items() if k in ALLOWED_FIELDS}
        m2m_updates = {k: v for k, v in fields.items() if k in ALLOWED_M2M}

        org = request.profile.org
        qs = Case.objects.filter(pk__in=ids, org=org)

        try:
            with transaction.atomic():
                updated_count = 0
                for case in qs:
                    changed = False
                    for k, v in scalar_updates.items():
                        setattr(case, k, v)
                        changed = True
                    if changed:
                        case.save()
                    for m2m_field, model in ALLOWED_M2M.items():
                        if m2m_field in m2m_updates:
                            related_ids = m2m_updates[m2m_field] or []
                            related = list(
                                model.objects.filter(pk__in=related_ids, org=org)
                            )
                            getattr(case, m2m_field).set(related)
                            changed = True
                    if changed:
                        updated_count += 1
        except ValidationError as exc:
            return Response(
                {
                    "error": True,
                    "errors": (
                        exc.message_dict
                        if hasattr(exc, "message_dict")
                        else exc.messages
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"error": False, "updated": updated_count},
            status=status.HTTP_200_OK,
        )


class BulkDeleteCasesView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def post(self, request):
        ids = request.data.get("ids") or []
        if not ids:
            return Response(
                {"error": True, "errors": "ids required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        org = request.profile.org
        # Snapshot the cases so we can emit Activity rows after the bulk update
        # — queryset.update() bypasses signals.
        qs = Case.objects.filter(pk__in=ids, org=org, is_active=True)
        target_cases = list(qs.values("id", "name"))
        deleted_count = qs.update(is_active=False)
        if target_cases:
            Activity.objects.bulk_create(
                [
                    Activity(
                        user=request.profile,
                        action="DELETE",
                        entity_type="Case",
                        entity_id=case["id"],
                        entity_name=(case["name"] or "")[:255],
                        metadata={"bulk": True},
                        org_id=org.id,
                    )
                    for case in target_cases
                ]
            )
        return Response(
            {"error": False, "deleted": deleted_count},
            status=status.HTTP_200_OK,
        )
