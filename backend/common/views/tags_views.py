from django.utils.text import slugify
from drf_spectacular.utils import extend_schema, inline_serializer

from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common import swagger_params
from common.models import Tags
from common.serializer import TagsSerializer


class TagsListView(APIView, LimitOffsetPagination):
    model = Tags
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by(
            "-created_at"
        )
        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))

        context = {}
        results_tags = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        tags = TagsSerializer(results_tags, many=True).data
        if results_tags:
            offset = queryset.filter(id__gte=results_tags[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update({"tags_count": self.count, "offset": offset})
        context["tags"] = tags
        return context

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_list",
        parameters=swagger_params.organization_params,
        responses={200: inline_serializer(
            name="TagsListResponse",
            fields={
                "per_page": serializers.IntegerField(),
                "page_number": serializers.ListField(),
                "tags_count": serializers.IntegerField(),
                "offset": serializers.IntegerField(allow_null=True),
                "tags": TagsSerializer(many=True),
            }
        )},
    )
    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_create",
        request=TagsSerializer,
        parameters=swagger_params.organization_params,
        responses={200: inline_serializer(
            name="TagCreateResponse",
            fields={"error": serializers.BooleanField(), "message": serializers.CharField(), "tag": TagsSerializer()}
        )},
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        name = params.get("name", "").strip()

        if not name:
            return Response(
                {"error": True, "errors": {"name": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slug = slugify(name)

        # Check for duplicate tag in this org
        if Tags.objects.filter(slug=slug, org=request.profile.org).exists():
            return Response(
                {"error": True, "errors": {"name": ["A tag with this name already exists."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tag = Tags.objects.create(
            name=name,
            slug=slug,
            org=request.profile.org,
            created_by=request.profile,
        )

        return Response(
            {"error": False, "message": "Tag Created Successfully", "tag": TagsSerializer(tag).data},
            status=status.HTTP_201_CREATED,
        )


class TagsDetailView(APIView):
    model = Tags
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_retrieve",
        parameters=swagger_params.organization_params,
        responses={200: inline_serializer(
            name="TagDetailResponse",
            fields={"tag": TagsSerializer()}
        )},
    )
    def get(self, request, pk, **kwargs):
        try:
            tag_obj = self.get_object(pk)
        except Tags.DoesNotExist:
            return Response(
                {"error": True, "errors": "Tag not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        context = {}
        context["tag"] = TagsSerializer(tag_obj).data
        return Response(context)

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_update",
        request=TagsSerializer,
        parameters=swagger_params.organization_params,
        responses={200: inline_serializer(
            name="TagUpdateResponse",
            fields={"error": serializers.BooleanField(), "message": serializers.CharField(), "tag": TagsSerializer()}
        )},
    )
    def put(self, request, pk, *args, **kwargs):
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
        if Tags.objects.filter(slug=slug, org=request.profile.org).exclude(pk=pk).exists():
            return Response(
                {"error": True, "errors": {"name": ["A tag with this name already exists."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tag_obj.name = name
        tag_obj.slug = slug
        tag_obj.updated_by = request.profile
        tag_obj.save()

        return Response(
            {"error": False, "message": "Tag Updated Successfully", "tag": TagsSerializer(tag_obj).data},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Tags"],
        operation_id="tags_destroy",
        parameters=swagger_params.organization_params,
        responses={200: inline_serializer(
            name="TagDeleteResponse",
            fields={"error": serializers.BooleanField(), "message": serializers.CharField()}
        )},
    )
    def delete(self, request, pk, **kwargs):
        try:
            tag_obj = self.get_object(pk)
        except Tags.DoesNotExist:
            return Response(
                {"error": True, "errors": "Tag not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        tag_obj.delete()
        return Response(
            {"error": False, "message": "Tag Deleted Successfully"},
            status=status.HTTP_200_OK,
        )
