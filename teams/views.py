from teams import swagger_params
from teams.models import Teams
from teams.tasks import update_team_users, remove_users
from teams.serializer import TeamsSerializer, TeamCreateSerializer
from common.models import Profile
from common.custom_auth import JSONWebTokenAuthentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from drf_yasg.utils import swagger_auto_schema
import json


class TeamsListView(APIView, LimitOffsetPagination):
    model = Teams
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(org=self.request.org).order_by('-id')
        if params:
            if params.get("team_name"):
                queryset = queryset.filter(
                    name__icontains=params.get("team_name")
                )
            if params.get("created_by"):
                queryset = queryset.filter(created_by=params.get("created_by"))
            if params.get("assigned_users"):
                queryset = queryset.filter(
                    users__id__in=json.loads(params.get("assigned_users"))
                )

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
        page_number = int(self.offset / 10) + 1,
        context["page_number"] = page_number
        context.update(
            {
                "teams_count": self.count,
                "offset": offset
            }
        )
        context["teams"] = teams
        return context

    @swagger_auto_schema(
        tags=["Teams"], manual_parameters=swagger_params.teams_list_get_params
    )
    def get(self, request, *args, **kwargs):
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

    @swagger_auto_schema(
        tags=["Teams"], manual_parameters=swagger_params.teams_create_post_params
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
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )

        serializer = TeamCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            team_obj = serializer.save(created_by=request.profile, org=request.org)

            if params.get("assign_users"):
                assinged_to_list = json.loads(params.get("assign_users"))
                profiles = Profile.objects.filter(id__in=assinged_to_list, org=request.org)
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
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.org)

    @swagger_auto_schema(
        tags=["Teams"], manual_parameters=swagger_params.organization_params
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

    @swagger_auto_schema(
        tags=["Teams"], manual_parameters=swagger_params.teams_create_post_params
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
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
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
                assinged_to_list = json.loads(params.get("assign_users"))
                profiles = Profile.objects.filter(id__in=assinged_to_list, org=request.org)
                if profiles:
                    team_obj.users.add(*profiles)
            update_team_users.delay(pk)
            latest_users = team_obj.get_users()
            for user in actual_users:
                if user not in latest_users:
                    removed_users.append(user)
            remove_users.delay(removed_users, pk)
            return Response(
                {"error": False, "message": "Team Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Teams"], manual_parameters=swagger_params.organization_params
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
