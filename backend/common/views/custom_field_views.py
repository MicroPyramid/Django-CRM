"""Generic custom-field definition CRUD endpoints.

Lives in `common` so all entity apps (Cases first, Leads/Contacts/etc. later)
can drive their per-entity schemas through one API.

See docs/cases/tier1/custom-fields.md.
"""

from django.apps import apps
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import CustomFieldDefinition
from common.permissions import HasOrgContext, is_org_admin
from common.serializer import CustomFieldDefinitionSerializer

# Each custom-field target_model → the (app_label, model) whose rows store the
# values in a `custom_fields` JSONField. Mirrors custom_fields.SUPPORTED_TARGETS;
# used to count how many records predate a field (see _records_missing_map).
_TARGET_MODELS = {
    "Account": ("accounts", "Account"),
    "Case": ("cases", "Case"),
    "Contact": ("contacts", "Contact"),
    "Estimate": ("invoices", "Estimate"),
    "Invoice": ("invoices", "Invoice"),
    "Lead": ("leads", "Lead"),
    "Opportunity": ("opportunity", "Opportunity"),
    "RecurringInvoice": ("invoices", "RecurringInvoice"),
    "Task": ("tasks", "Task"),
}


def _admin_required():
    return Response(
        {"error": True, "errors": "Admin access required"},
        status=status.HTTP_403_FORBIDDEN,
    )


def _resolve_target_model(target_model):
    ref = _TARGET_MODELS.get(target_model)
    if ref is None:
        return None
    try:
        return apps.get_model(*ref)
    except LookupError:
        return None


def _records_missing_map(org, definitions):
    """Map {definition_id(str): records_missing_value} for `definitions`.

    A record "has a value" for a field when its `custom_fields` JSON carries the
    field's key (the value pipeline never stores empty/None), so
    missing = <org records of that target_model> − <those carrying the key>.
    Marking a field required only binds new writes, so this counts the rows that
    predate the rule. Every query is explicitly `org=`-scoped. RLS is inert for
    the app's DB role in dev/test, so the ORM filter is what keeps another org's
    record counts (and their existence) out of this number.
    """
    by_model = {}
    for defn in definitions:
        by_model.setdefault(defn.target_model, []).append(defn)

    result = {}
    for target_model, defs in by_model.items():
        model = _resolve_target_model(target_model)
        if model is None:
            # Unknown/unwired target, can't count, report zero rather than 500.
            for defn in defs:
                result[str(defn.id)] = 0
            continue
        total = model.objects.filter(org=org).count()
        for defn in defs:
            with_value = model.objects.filter(
                org=org, custom_fields__has_key=defn.key
            ).count()
            result[str(defn.id)] = max(total - with_value, 0)
    return result


def _cf_totals(definitions, missing_by_id):
    """Stat-card totals over the org's whole definition set."""
    active = [d for d in definitions if d.is_active]
    return {
        "count": len(definitions),
        "active": len(active),
        "models_extended": len({d.target_model for d in active}),
        # Matches the page's gap banner: any required field with rows missing it.
        "required_with_gaps": sum(
            1
            for d in definitions
            if d.is_required and missing_by_id.get(str(d.id), 0) > 0
        ),
    }


class CustomFieldDefinitionListCreateView(APIView):
    """GET ?target_model=Case lists definitions; POST creates one (admin)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["CustomFields"],
        responses={200: CustomFieldDefinitionSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        org = request.profile.org
        qs = CustomFieldDefinition.objects.filter(org=org)
        target_model = request.query_params.get("target_model")
        if target_model:
            qs = qs.filter(target_model=target_model)
        if request.query_params.get("active_only") == "true":
            qs = qs.filter(is_active=True)

        rows = CustomFieldDefinitionSerializer(qs, many=True).data

        # `records_missing_value` costs one COUNT over the org's whole record
        # set per definition, plus one per target model, a `custom_fields ?
        # key` scan of every Lead the org has, for each field. The settings
        # page needs those numbers; a record page that only wants labels and
        # types to render a form does not, and making it pay for the stat cards
        # puts N+1 full scans on every lead view. `include_counts=false` opts
        # out. The default is unchanged, so existing callers are unaffected.
        if request.query_params.get("include_counts") == "false":
            return Response({"definitions": rows, "totals": None})

        # records_missing_value + totals are computed over the org's FULL
        # definition set (independent of the target_model/active_only filters)
        # so the stat cards stay correct when the list is filtered.
        all_defs = list(CustomFieldDefinition.objects.filter(org=org))
        missing_by_id = _records_missing_map(org, all_defs)

        for row in rows:
            row["records_missing_value"] = missing_by_id.get(row["id"], 0)

        return Response(
            {
                "definitions": rows,
                "totals": _cf_totals(all_defs, missing_by_id),
            }
        )

    @extend_schema(
        tags=["CustomFields"],
        request=CustomFieldDefinitionSerializer,
        responses={201: CustomFieldDefinitionSerializer},
    )
    def post(self, request, *args, **kwargs):
        if not is_org_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        serializer = CustomFieldDefinitionSerializer(
            data=request.data, context={"org": org}
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(org=org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomFieldDefinitionDetailView(APIView):
    """GET / PUT / DELETE one definition. DELETE soft-deletes (is_active=False)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get_object(self, pk, org):
        return CustomFieldDefinition.objects.filter(pk=pk, org=org).first()

    @extend_schema(
        tags=["CustomFields"], responses={200: CustomFieldDefinitionSerializer}
    )
    def get(self, request, pk, *args, **kwargs):
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Custom field not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CustomFieldDefinitionSerializer(obj).data)

    @extend_schema(
        tags=["CustomFields"],
        request=CustomFieldDefinitionSerializer,
        responses={200: CustomFieldDefinitionSerializer},
    )
    def put(self, request, pk, *args, **kwargs):
        if not is_org_admin(request.profile):
            return _admin_required()
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Custom field not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CustomFieldDefinitionSerializer(
            obj,
            data=request.data,
            partial=True,
            context={"org": request.profile.org},
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["CustomFields"],
        responses={
            200: inline_serializer(
                name="CustomFieldDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, *args, **kwargs):
        if not is_org_admin(request.profile):
            return _admin_required()
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Custom field not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Soft delete: historical values on entities stay readable; the field
        # just stops appearing in admin UIs and stops accepting new writes.
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(
            {"error": False, "message": "Custom field deactivated"},
            status=status.HTTP_200_OK,
        )
