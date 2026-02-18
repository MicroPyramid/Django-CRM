from datetime import date

from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Profile
from common.permissions import HasOrgContext
from opportunity.models import SalesGoal
from opportunity.serializer import SalesGoalCreateSerializer, SalesGoalSerializer


class SalesGoalListView(APIView, LimitOffsetPagination):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_queryset(self, request):
        org = request.profile.org
        queryset = SalesGoal.objects.filter(org=org)

        is_admin = request.profile.role == "ADMIN" or request.user.is_superuser
        if not is_admin:
            queryset = queryset.filter(
                Q(assigned_to=request.profile)
                | Q(team__in=request.profile.user_teams.all())
            )

        params = request.query_params
        if params.get("active") == "true":
            queryset = queryset.filter(is_active=True)
        if params.get("current") == "true":
            today = date.today()
            queryset = queryset.filter(
                period_start__lte=today, period_end__gte=today
            )
        if params.get("assigned_to"):
            queryset = queryset.filter(assigned_to_id=params["assigned_to"])
        if params.get("team"):
            queryset = queryset.filter(team_id=params["team"])
        if params.get("period_type"):
            queryset = queryset.filter(period_type=params["period_type"])
        if params.get("search"):
            queryset = queryset.filter(name__icontains=params["search"])

        return queryset.distinct()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request)
        results = self.paginate_queryset(queryset, request, view=self)
        serializer = SalesGoalSerializer(results, many=True)

        total_count = self.count
        offset = None
        if results:
            offset = queryset.filter(id__gte=results[-1].id).count()
            if offset == total_count:
                offset = None

        return Response(
            {
                "goals": serializer.data,
                "goals_count": total_count,
                "offset": offset,
                "per_page": 10,
            }
        )

    def post(self, request, *args, **kwargs):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can create goals."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SalesGoalCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                org=request.profile.org,
                created_by=request.profile.user,
            )
            return Response(
                {"error": False, "message": "Goal Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SalesGoalDetailView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk, request):
        return SalesGoal.objects.filter(
            id=pk, org=request.profile.org
        ).first()

    def get(self, request, pk, *args, **kwargs):
        goal = self.get_object(pk, request)
        if not goal:
            return Response(
                {"error": True, "errors": "Goal not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        is_admin = request.profile.role == "ADMIN" or request.user.is_superuser
        if not is_admin:
            if goal.assigned_to != request.profile and (
                not goal.team or goal.team not in request.profile.user_teams.all()
            ):
                return Response(
                    {"error": True, "errors": "You do not have permission."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        serializer = SalesGoalSerializer(goal)
        return Response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can update goals."},
                status=status.HTTP_403_FORBIDDEN,
            )
        goal = self.get_object(pk, request)
        if not goal:
            return Response(
                {"error": True, "errors": "Goal not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SalesGoalCreateSerializer(
            goal, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"error": False, "message": "Goal Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk, *args, **kwargs):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can delete goals."},
                status=status.HTTP_403_FORBIDDEN,
            )
        goal = self.get_object(pk, request)
        if not goal:
            return Response(
                {"error": True, "errors": "Goal not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        goal.delete()
        return Response(
            {"error": False, "message": "Goal Deleted Successfully"},
            status=status.HTTP_200_OK,
        )


class SalesGoalLeaderboardView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request, *args, **kwargs):
        org = request.profile.org
        today = date.today()

        period_type = request.query_params.get("period_type", "MONTHLY")

        goals = SalesGoal.objects.filter(
            org=org,
            is_active=True,
            period_type=period_type,
            period_start__lte=today,
            period_end__gte=today,
            assigned_to__isnull=False,
        ).select_related("assigned_to", "assigned_to__user")

        leaderboard = []
        for goal in goals:
            progress = goal.compute_progress()
            if goal.target_value and goal.target_value != 0:
                percent = min(
                    int(float(progress) / float(goal.target_value) * 100), 100
                )
            else:
                percent = 0
            leaderboard.append(
                {
                    "goal_id": str(goal.id),
                    "goal_name": goal.name,
                    "user": {
                        "id": str(goal.assigned_to.id),
                        "name": goal.assigned_to.user.email,
                        "email": goal.assigned_to.user.email,
                    },
                    "target": float(goal.target_value),
                    "achieved": float(progress),
                    "percent": percent,
                }
            )

        leaderboard.sort(key=lambda x: x["percent"], reverse=True)

        for i, entry in enumerate(leaderboard, 1):
            entry["rank"] = i

        return Response({"leaderboard": leaderboard})
