from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from teams import swagger_params
from teams.models import Teams
from teams.tasks import update_team_users, remove_users
from teams.serializer import TeamsSerializer, TeamCreateSerializer
from common.models import User
from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import UserSerializer

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
import json

class TeamsListView(APIView):
    model = Teams
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = (
            self.model.objects.filter(company=self.request.company)            
        )

        request_post = params
        if request_post:
            if request_post.get("team_name"):
                queryset = queryset.filter(
                    name__icontains=request_post.get("team_name")
                )
            if request_post.get("created_by"):
                queryset = queryset.filter(
                    created_by=request_post.get("created_by"))
            if request_post.get("assigned_users"):
                queryset = queryset.filter(
                    users__id__in=json.loads(request_post.get("assigned_users"))                )

        context = {}
        search = False
        if (
            params.get("team_name")
            or params.get("created_by")
            or params.get("assigned_users")
        ):
            search = True
        context["search"] = search

        context["teams"] = TeamsSerializer(
            queryset.distinct(), many=True).data
        users = User.objects.filter(
                is_active=True,
                company=self.request.company).order_by("id")
        context["users"] = UserSerializer(users, many=True).data
        return context

    @swagger_auto_schema(
        tags=["Teams"],
        manual_parameters=swagger_params.teams_list_get_params
    )
    def get(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response({
                "error": True,
                "errors": "You don't have permission to perform this action."},
                status = status.HTTP_403_FORBIDDEN
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Teams"],
        manual_parameters=swagger_params.teams_create_post_params
    )
    def post(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response({
                "error": True,
                "errors": "You don't have permission to perform this action."},
                status = status.HTTP_403_FORBIDDEN
            )
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )

        serializer = TeamCreateSerializer(
            data=params, request_obj=request)
        data = {}
        if serializer.is_valid():
            team_obj = serializer.save(
                created_by=request.user, company=request.company)

            if params.get("assign_users"):
                assinged_to_users_ids = json.loads(params.get("assign_users"))
                for user_id in assinged_to_users_ids:
                    user = User.objects.filter(id=user_id, company=request.company)
                    if user:                            
                        team_obj.users.add(user_id)
                    else:
                        team_obj.delete()
                        data["users"] = "Please enter valid user"
                        return Response({
                            "error": True,
                            "errors":data})     
            return Response({"error": False,
                             "message": "Team Created Successfully"},
                            status=status.HTTP_200_OK)
        return Response({"error": True,
                         "errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

class TeamsDetailView(APIView):
    model = Teams
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Teams"],
        manual_parameters=swagger_params.teams_delete_params
    )
    def get(self, request, pk, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response({
                "error": True,
                "errors": "You don't have permission to perform this action."},
                status = status.HTTP_403_FORBIDDEN
            )
        self.team_obj = self.get_object(pk)
        if self.team_obj.company != request.company:
            return Response(
                {"error": True,
                 "errors": "User company doesnot match with header...."}
            )
        context = {}
        context["team"] = TeamsSerializer(self.team_obj).data
        context["users"] = UserSerializer(
            User.objects.filter(
                is_active=True, company=self.request.company
                ).order_by("email"), many=True
        ).data
        return Response(context)

    @swagger_auto_schema(
        tags=["Teams"],
        manual_parameters=swagger_params.teams_create_post_params
    )
    def put(self, request, pk, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response({
                "error": True,
                "errors": "You don't have permission to perform this action."},
                status = status.HTTP_403_FORBIDDEN
            )
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        self.team = self.get_object(pk)
        if self.team.company != request.company:
            return Response(
                {"error": True,
                 "errors": "User company doesnot match with header...."}
            )
        actual_users = self.team.get_users()
        removed_users = []
        serializer = TeamCreateSerializer(
            data=params, instance=self.team, request_obj=request)
        data = {}
        if serializer.is_valid():
            team_obj = serializer.save()

            team_obj.users.clear()
            if params.get("assign_users"):
                assinged_to_users_ids = json.loads(params.get("assign_users"))
                for user_id in assinged_to_users_ids:
                    user = User.objects.filter(id=user_id, company=request.company)
                    if user:                            
                        team_obj.users.add(user_id)
                    else:
                        data["users"] = "Please enter valid user"
                        return Response({
                            "error": True,
                            "errors":data})
            update_team_users.delay(pk)
            latest_users = team_obj.get_users()
            for user in actual_users:
                if user in latest_users:
                    pass
                else:
                    removed_users.append(user)
            remove_users.delay(removed_users, pk)
            return Response({"error": False,
                             "message": "Team Updated Successfully"},
                            status=status.HTTP_200_OK)
        return Response({"error": True,
                         "errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Teams"],
        manual_parameters=swagger_params.teams_delete_params
    )
    def delete(self, request, pk, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response({
                "error": True,
                "errors": "You don't have permission to perform this action."},
                status = status.HTTP_403_FORBIDDEN
            )
        self.team_obj = self.get_object(pk)
        if self.team_obj.company != request.company:
            return Response(
                {"error": True,
                 "errors": "User company doesnot match with header...."}
            )
        self.team_obj.delete()
        return Response({
            "error": False,
            "message": "Team Deleted Successfully"
        })