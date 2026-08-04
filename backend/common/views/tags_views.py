from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from cases.models import Case
from common import swagger_params
from common.models import Tags
from common.permissions import HasOrgContext
from common.serializer import TagsSerializer
from leads.models import Lead
from opportunity.models import Opportunity

# The models a tag can be applied to, paired with the usage key the settings
# page shows. Each is org-scoped and carries a `tags` M2M back to Tags.
_TAGGABLE = (
    ("accounts", Account),
    ("leads", Lead),
    ("opportunities", Opportunity),
    ("cases", Case),
)


def _usage_subquery(model, org):
    """Per-tag count of `model` rows in `org` that carry the tag.

    One correlated subquery per relation rather than four `Count`s on a single
    query: joining all four M2M through-tables at once multiplies rows, and a
    subquery keeps each count independent (the subquery-rollup rule). Filtered
    by `org` explicitly. Usage is a per-org fact and must not lean on RLS,
    which is inert for the app's DB role in dev/test.
    """
    return Coalesce(
        Subquery(
            model.objects.filter(tags=OuterRef("pk"), org=org)
            .order_by()
            .values("tags")
            .annotate(c=Count("pk"))
            .values("c"),
            output_field=IntegerField(),
        ),
        0,
    )


def _annotated_tags(org):
    """Org tags annotated with a `_u_<key>` usage count per taggable model."""
    return Tags.objects.filter(org=org).annotate(
        **{f"_u_{key}": _usage_subquery(model, org) for key, model in _TAGGABLE}
    )


def _tag_totals(org):
    """Counts over ALL org tags, independent of the list's active/name filters,
    so the stat cards stay meaningful when the list is filtered."""
    all_tags = list(_annotated_tags(org))
    active = [t for t in all_tags if t.is_active]

    def total_usage(tag):
        return sum(getattr(tag, f"_u_{key}") for key, _ in _TAGGABLE)

    return {
        "count": len(all_tags),
        "active": len(active),
        # Active tags applied to nothing across the models in _TAGGABLE: the
        # "unused" figure on the settings stat card. There is no hard delete
        # on a tag at all, here or anywhere else: TagsDetailView.delete only
        # flips is_active to False, so this count is not measuring what is
        # safe to remove, only what is not currently referenced.
        "unused": sum(1 for t in active if total_usage(t) == 0),
    }


class TagsListView(APIView, LimitOffsetPagination):
    model = Tags
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_queryset(self):
        """Get tags queryset (with usage annotations) and optional filtering."""
        params = self.request.query_params
        queryset = _annotated_tags(self.request.profile.org)

        # By default, only show active tags
        # Admin can see archived tags with ?include_archived=true
        include_archived = params.get("include_archived", "").lower() == "true"
        if not include_archived:
            queryset = queryset.filter(is_active=True)

        # Filter by name if provided
        if params.get("name"):
            queryset = queryset.filter(name__icontains=params.get("name"))

        return queryset.order_by("name")

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_list",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TagsListResponse",
                fields={
                    "tags_count": serializers.IntegerField(),
                    "tags": TagsSerializer(many=True),
                    "totals": serializers.DictField(),
                },
            )
        },
    )
    def get(self, request, *args, **kwargs):
        """List tags for the org, each with per-model usage counts, plus totals."""
        tags_qs = list(self.get_queryset())
        rows = TagsSerializer(tags_qs, many=True).data
        # Attach usage from the annotations (serializer order matches the qs).
        for row, obj in zip(rows, tags_qs):
            row["usage"] = {key: getattr(obj, f"_u_{key}") for key, _ in _TAGGABLE}
        return Response(
            {
                "tags_count": len(rows),
                "tags": rows,
                "totals": _tag_totals(request.profile.org),
            }
        )

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_create",
        request=TagsSerializer,
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TagCreateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "tag": TagsSerializer(),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        """Create a new tag (admin only)."""
        # Admin only for create
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can create tags"},
                status=status.HTTP_403_FORBIDDEN,
            )

        params = request.data
        name = params.get("name", "").strip()

        if not name:
            return Response(
                {"error": True, "errors": {"name": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slug = slugify(name)

        # Check for duplicate tag in this org (including archived)
        existing = Tags.objects.filter(slug=slug, org=request.profile.org).first()
        if existing:
            if not existing.is_active:
                # Reactivate archived tag with same name
                existing.is_active = True
                existing.color = params.get("color", existing.color)
                existing.description = params.get("description", existing.description)
                existing.updated_by = request.user
                existing.save()
                return Response(
                    {
                        "error": False,
                        "message": "Tag reactivated successfully",
                        "tag": TagsSerializer(existing).data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "error": True,
                    "errors": {"name": ["A tag with this name already exists."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get color and description from request
        color = params.get("color", "blue")
        description = params.get("description", "")

        # Validate color
        valid_colors = [c[0] for c in Tags.COLOR_CHOICES]
        if color not in valid_colors:
            color = "blue"

        tag = Tags.objects.create(
            name=name,
            slug=slug,
            color=color,
            description=description,
            org=request.profile.org,
            created_by=request.user,
        )

        return Response(
            {
                "error": False,
                "message": "Tag Created Successfully",
                "tag": TagsSerializer(tag).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TagsDetailView(APIView):
    model = Tags
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_retrieve",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TagDetailResponse", fields={"tag": TagsSerializer()}
            )
        },
    )
    def get(self, request, pk, **kwargs):
        """Get a single tag by ID."""
        try:
            tag_obj = self.get_object(pk)
        except Tags.DoesNotExist:
            return Response(
                {"error": True, "errors": "Tag not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"tag": TagsSerializer(tag_obj).data})

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_update",
        request=TagsSerializer,
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TagUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "tag": TagsSerializer(),
                },
            )
        },
    )
    def put(self, request, pk, *args, **kwargs):
        """Update a tag (admin only)."""
        # Admin only
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can update tags"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            tag_obj = self.get_object(pk)
        except Tags.DoesNotExist:
            return Response(
                {"error": True, "errors": "Tag not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        params = request.data
        name = params.get("name", "").strip()

        if not name:
            return Response(
                {"error": True, "errors": {"name": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slug = slugify(name)

        # Check for duplicate tag in this org (excluding current tag)
        if (
            Tags.objects.filter(slug=slug, org=request.profile.org)
            .exclude(pk=pk)
            .exists()
        ):
            return Response(
                {
                    "error": True,
                    "errors": {"name": ["A tag with this name already exists."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        tag_obj.name = name
        tag_obj.slug = slug

        # Update color if provided
        if "color" in params:
            color = params.get("color")
            valid_colors = [c[0] for c in Tags.COLOR_CHOICES]
            if color in valid_colors:
                tag_obj.color = color

        # Update description if provided
        if "description" in params:
            tag_obj.description = params.get("description", "")

        tag_obj.updated_by = request.user
        tag_obj.save()

        return Response(
            {
                "error": False,
                "message": "Tag Updated Successfully",
                "tag": TagsSerializer(tag_obj).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_archive",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TagArchiveResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, **kwargs):
        """Archive a tag - soft delete (admin only)."""
        # Admin only
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can archive tags"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            tag_obj = self.get_object(pk)
        except Tags.DoesNotExist:
            return Response(
                {"error": True, "errors": "Tag not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Soft delete - archive the tag
        tag_obj.is_active = False
        tag_obj.updated_by = request.user
        tag_obj.save()

        return Response(
            {"error": False, "message": "Tag archived successfully"},
            status=status.HTTP_200_OK,
        )


class TagsRestoreView(APIView):
    """Restore an archived tag."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_restore",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TagRestoreResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "tag": TagsSerializer(),
                },
            )
        },
    )
    def post(self, request, pk, **kwargs):
        """Restore an archived tag (admin only)."""
        # Admin only
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can restore tags"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            tag_obj = Tags.objects.get(pk=pk, org=request.profile.org)
        except Tags.DoesNotExist:
            return Response(
                {"error": True, "errors": "Tag not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tag_obj.is_active = True
        tag_obj.updated_by = request.user
        tag_obj.save()

        return Response(
            {
                "error": False,
                "message": "Tag restored successfully",
                "tag": TagsSerializer(tag_obj).data,
            },
            status=status.HTTP_200_OK,
        )
