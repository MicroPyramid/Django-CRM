from drf_spectacular.utils import extend_schema, inline_serializer

from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common import swagger_params
from common.models import Profile, Teams
from common.serializer import (
    TeamCreateSerializer,
    TeamsSerializer,
    TeamswaggerCreateSerializer,
)
from common.tasks import remove_users, update_team_users


class TeamsListView(APIView, LimitOffsetPagination):
    model = Teams
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by(
            "-id"
        )
        if params:
            if params.get("team_name"):
                queryset = queryset.filter(name__icontains=params.get("team_name"))
            if params.get("created_by"):
                queryset = queryset.filter(created_by=params.get("created_by"))
            if params.get("assigned_users"):
                queryset = queryset.filter(users__id__in=params.get("assigned_users"))

        context = {}
        results_teams = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        teams = TeamsSerializer(results_teams, many=True).data
        if results_teams:
            offset = queryset.filter(id__gte=results_teams[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update({"teams_count": self.count, "offset": offset})
        context["teams"] = teams
        return context

    @extend_schema(
        tags=["Teams"],
        operation_id="teams_list",
        parameters=swagger_params.teams_list_get_params,
        responses={
            200: inline_serializer(
                name="TeamsListResponse",
                fields={
                    "per_page": serializers.IntegerField(),
                    "page_number": serializers.ListField(),
                    "teams_count": serializers.IntegerField(),
                    "offset": serializers.IntegerField(allow_null=True),
                    "teams": TeamsSerializer(many=True),
                },
            )
        },
    )
    def get(self, *args, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Teams"],
        operation_id="teams_create",
        request=TeamswaggerCreateSerializer,
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TeamCreateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = self.request.data
        serializer = TeamCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            team_obj = serializer.save(org=request.profile.org)

            if params.get("assign_users"):
                assinged_to_list = params.get("users")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org
                )
                if profiles:
                    team_obj.users.add(*profiles)
            return Response(
                {"error": False, "message": "Team Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TeamsDetailView(APIView):
    model = Teams
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Teams"],
        operation_id="teams_retrieve",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TeamDetailResponse", fields={"team": TeamsSerializer()}
            )
        },
    )
    def get(self, request, pk, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.team_obj = self.get_object(pk)
        context = {}
        context["team"] = TeamsSerializer(self.team_obj).data
        return Response(context)

    @extend_schema(
        tags=["Teams"],
        operation_id="teams_update",
        request=TeamswaggerCreateSerializer,
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TeamUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def put(self, request, pk, *args, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = request.data
        self.team = self.get_object(pk)
        actual_users = self.team.get_users()
        removed_users = []
        serializer = TeamCreateSerializer(
            data=params, instance=self.team, request_obj=request
        )
        if serializer.is_valid():
            team_obj = serializer.save()

            team_obj.users.clear()
            if params.get("assign_users"):
                assinged_to_list = params.get("assign_users")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org
                )
                if profiles:
                    team_obj.users.add(*profiles)
            update_team_users.delay(pk, str(request.profile.org.id))
            latest_users = team_obj.get_users()
            for user in actual_users:
                if user not in latest_users:
                    removed_users.append(user)
            remove_users.delay(removed_users, pk, str(request.profile.org.id))
            return Response(
                {"error": False, "message": "Team Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Teams"],
        request=TeamswaggerCreateSerializer,
        parameters=swagger_params.organization_params,
        description="Partial Team Update",
        responses={
            200: inline_serializer(
                name="TeamPatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def patch(self, request, pk, *args, **kwargs):
        """Handle partial updates to a team."""
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = request.data
        self.team = self.get_object(pk)
        serializer = TeamCreateSerializer(
            data=params, instance=self.team, request_obj=request, partial=True
        )
        if serializer.is_valid():
            team_obj = serializer.save()
            return Response(
                {"error": False, "message": "Team Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Teams"],
        operation_id="teams_destroy",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TeamDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.team_obj = self.get_object(pk)
        self.team_obj.delete()
        return Response(
            {"error": False, "message": "Team Deleted Successfully"},
            status=status.HTTP_200_OK,
        )
