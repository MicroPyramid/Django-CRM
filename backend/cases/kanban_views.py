"""
Kanban views for case management.
Supports both status-based (default) and custom pipeline-based kanban boards.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Case, CasePipeline, CaseStage
from cases.serializer import (
    CaseKanbanCardSerializer,
    CaseMoveSerializer,
    CasePipelineListSerializer,
    CasePipelineSerializer,
    CaseStageSerializer,
)
from common.permissions import HasOrgContext
from common.utils import STATUS_CHOICE


class CaseKanbanView(APIView):
    """
    Kanban board view for cases.

    Supports two modes:
    1. Status-based (default): Groups cases by Case.status field
    2. Pipeline-based: Groups cases by CaseStage when pipeline_id is provided
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Cases Kanban"],
        operation_id="cases_kanban",
        parameters=[
            OpenApiParameter(name="org", required=True, type=str),
            OpenApiParameter(
                name="pipeline_id",
                description="Pipeline ID. If not provided, uses status-based columns",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="assigned_to",
                description="Filter by assigned user ID",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="priority",
                description="Filter by priority (Low/Normal/High/Urgent)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="case_type",
                description="Filter by case type (Question/Incident/Problem)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="search",
                description="Search in name and description",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="account",
                description="Filter by account ID",
                required=False,
                type=str,
            ),
        ],
    )
    def get(self, request):
        """Get kanban board data."""
        org = request.profile.org
        pipeline_id = request.query_params.get("pipeline_id")

        # Base queryset with filters
        queryset = (
            Case.objects.filter(org=org, is_active=True)
            .select_related("created_by", "stage", "account")
            .prefetch_related("assigned_to", "tags", "contacts")
        )

        # Apply permission filtering
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to=request.profile) | Q(created_by=request.profile.user)
            )

        # Apply search/filters
        queryset = self._apply_filters(queryset, request.query_params)

        if pipeline_id:
            return self._get_pipeline_kanban(queryset, pipeline_id, org)
        else:
            return self._get_status_kanban(queryset)

    def _apply_filters(self, queryset, params):
        """Apply common filters to queryset."""
        if params.get("assigned_to"):
            queryset = queryset.filter(assigned_to__id=params.get("assigned_to"))
        if params.get("priority"):
            queryset = queryset.filter(priority=params.get("priority"))
        if params.get("case_type"):
            queryset = queryset.filter(case_type=params.get("case_type"))
        if params.get("search"):
            search = params.get("search")
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if params.get("account"):
            queryset = queryset.filter(account_id=params.get("account"))
        if params.get("tags"):
            queryset = queryset.filter(tags__id=params.get("tags"))
        if params.get("created_at__gte"):
            queryset = queryset.filter(created_at__gte=params.get("created_at__gte"))
        if params.get("created_at__lte"):
            queryset = queryset.filter(created_at__lte=params.get("created_at__lte"))
        return queryset.distinct()

    def _get_status_kanban(self, queryset):
        """Build kanban data using Case.status as columns."""
        # Define column order and colors matching case workflow
        status_config = {
            "New": {"order": 1, "color": "#3B82F6", "type": "open"},
            "Assigned": {"order": 2, "color": "#8B5CF6", "type": "open"},
            "Pending": {"order": 3, "color": "#F59E0B", "type": "open"},
            "Closed": {"order": 4, "color": "#22C55E", "type": "closed"},
            "Rejected": {"order": 5, "color": "#EF4444", "type": "rejected"},
            "Duplicate": {"order": 6, "color": "#6B7280", "type": "rejected"},
        }

        columns = []
        for status_value, label in STATUS_CHOICE:
            config = status_config.get(
                status_value, {"order": 99, "color": "#6B7280", "type": "open"}
            )
            cases = queryset.filter(status=status_value).order_by(
                "kanban_order", "-created_at"
            )

            columns.append(
                {
                    "id": status_value,
                    "name": label,
                    "order": config["order"],
                    "color": config["color"],
                    "stage_type": config["type"],
                    "is_status_column": True,
                    "wip_limit": None,
                    "case_count": cases.count(),
                    "cases": CaseKanbanCardSerializer(cases[:100], many=True).data,
                }
            )

        columns.sort(key=lambda x: x["order"])

        return Response(
            {
                "mode": "status",
                "pipeline": None,
                "columns": columns,
                "total_cases": queryset.count(),
            }
        )

    def _get_pipeline_kanban(self, queryset, pipeline_id, org):
        """Build kanban data using CasePipeline stages as columns."""
        pipeline = get_object_or_404(
            CasePipeline, pk=pipeline_id, org=org, is_active=True
        )

        queryset = queryset.filter(stage__pipeline=pipeline)

        columns = []
        for stage in pipeline.stages.all().order_by("order"):
            cases = queryset.filter(stage=stage).order_by("kanban_order", "-created_at")

            columns.append(
                {
                    "id": str(stage.id),
                    "name": stage.name,
                    "order": stage.order,
                    "color": stage.color,
                    "stage_type": stage.stage_type,
                    "wip_limit": stage.wip_limit,
                    "maps_to_status": stage.maps_to_status,
                    "is_status_column": False,
                    "case_count": cases.count(),
                    "cases": CaseKanbanCardSerializer(cases[:100], many=True).data,
                }
            )

        return Response(
            {
                "mode": "pipeline",
                "pipeline": CasePipelineListSerializer(pipeline).data,
                "columns": columns,
                "total_cases": queryset.count(),
            }
        )


class CaseMoveView(APIView):
    """Move a case to a different stage/status and update order."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Cases Kanban"],
        operation_id="case_move",
        request=CaseMoveSerializer,
    )
    @transaction.atomic
    def patch(self, request, pk):
        """Move case to different column and/or position."""
        org = request.profile.org
        case = get_object_or_404(Case, pk=pk, org=org)

        # Permission check
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            if not (
                request.profile.user == case.created_by
                or request.profile in case.assigned_to.all()
            ):
                return Response(
                    {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                )

        serializer = CaseMoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Handle stage change
        if "stage_id" in data:
            if data["stage_id"]:
                stage = get_object_or_404(CaseStage, pk=data["stage_id"], org=org)

                # Check WIP limit
                if stage.wip_limit:
                    current_count = stage.cases.exclude(pk=case.pk).count()
                    if current_count >= stage.wip_limit:
                        return Response(
                            {
                                "error": f"Stage '{stage.name}' has reached its WIP limit of {stage.wip_limit}"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                case.stage = stage

                # Auto-update status if stage has maps_to_status
                if stage.maps_to_status:
                    case.status = stage.maps_to_status
            else:
                case.stage = None

        # Handle status change (for status-based kanban)
        if "status" in data:
            case.status = data["status"]

        # Calculate new order
        new_order = self._calculate_order(data, case, org)
        case.kanban_order = new_order

        case.save()

        return Response(
            {
                "error": False,
                "message": "Case moved successfully",
                "case": CaseKanbanCardSerializer(case).data,
            }
        )

    def _calculate_order(self, data, case, org):
        """Calculate the new kanban_order based on position hints."""
        if "kanban_order" in data:
            return data["kanban_order"]

        above_id = data.get("above_case_id")
        below_id = data.get("below_case_id")

        if above_id and below_id:
            above_case = Case.objects.filter(pk=above_id, org=org).first()
            below_case = Case.objects.filter(pk=below_id, org=org).first()
            if above_case and below_case:
                return (above_case.kanban_order + below_case.kanban_order) / 2

        if above_id:
            above_case = Case.objects.filter(pk=above_id, org=org).first()
            if above_case:
                if case.stage:
                    next_case = (
                        Case.objects.filter(
                            org=org,
                            stage=case.stage,
                            kanban_order__gt=above_case.kanban_order,
                        )
                        .order_by("kanban_order")
                        .first()
                    )
                else:
                    next_case = (
                        Case.objects.filter(
                            org=org,
                            status=case.status,
                            stage__isnull=True,
                            kanban_order__gt=above_case.kanban_order,
                        )
                        .order_by("kanban_order")
                        .first()
                    )

                if next_case:
                    return (above_case.kanban_order + next_case.kanban_order) / 2
                return above_case.kanban_order + Decimal("1000")

        if below_id:
            below_case = Case.objects.filter(pk=below_id, org=org).first()
            if below_case:
                return below_case.kanban_order - Decimal("1000")

        # Default: append to end
        if case.stage:
            last_case = (
                Case.objects.filter(stage=case.stage, org=org)
                .exclude(pk=case.pk)
                .order_by("-kanban_order")
                .first()
            )
        else:
            last_case = (
                Case.objects.filter(status=case.status, stage__isnull=True, org=org)
                .exclude(pk=case.pk)
                .order_by("-kanban_order")
                .first()
            )

        if last_case:
            return last_case.kanban_order + Decimal("1000")
        return Decimal("1000")


# Pipeline CRUD Views (following Lead/Task pattern)
class CasePipelineListCreateView(APIView):
    """List and create case pipelines."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Case Pipelines"], responses={200: CasePipelineListSerializer(many=True)}
    )
    def get(self, request):
        """List all pipelines for the organization."""
        org = request.profile.org
        pipelines = CasePipeline.objects.filter(org=org, is_active=True)
        serializer = CasePipelineListSerializer(pipelines, many=True)
        return Response({"pipelines": serializer.data})

    @extend_schema(
        tags=["Case Pipelines"],
        request=CasePipelineSerializer,
        responses={201: CasePipelineSerializer},
    )
    def post(self, request):
        """Create a new pipeline."""
        org = request.profile.org

        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Only admins can create pipelines"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CasePipelineSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pipeline = serializer.save(org=org, created_by=request.user)

        # Create default stages if requested
        if request.data.get("create_default_stages", True):
            default_stages = [
                {
                    "name": "New",
                    "order": 1,
                    "color": "#3B82F6",
                    "stage_type": "open",
                    "maps_to_status": "New",
                },
                {
                    "name": "Assigned",
                    "order": 2,
                    "color": "#8B5CF6",
                    "stage_type": "open",
                    "maps_to_status": "Assigned",
                },
                {
                    "name": "In Progress",
                    "order": 3,
                    "color": "#F59E0B",
                    "stage_type": "open",
                    "maps_to_status": "Pending",
                },
                {
                    "name": "Resolved",
                    "order": 4,
                    "color": "#22C55E",
                    "stage_type": "closed",
                    "maps_to_status": "Closed",
                },
                {
                    "name": "Rejected",
                    "order": 5,
                    "color": "#EF4444",
                    "stage_type": "rejected",
                    "maps_to_status": "Rejected",
                },
            ]
            for stage_data in default_stages:
                CaseStage.objects.create(
                    pipeline=pipeline, org=org, created_by=request.user, **stage_data
                )

        # Refresh to include created stages
        pipeline.refresh_from_db()
        return Response(
            CasePipelineSerializer(pipeline).data, status=status.HTTP_201_CREATED
        )


class CasePipelineDetailView(APIView):
    """Retrieve, update, delete a pipeline."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk, org):
        return get_object_or_404(CasePipeline, pk=pk, org=org)

    @extend_schema(tags=["Case Pipelines"], responses={200: CasePipelineSerializer})
    def get(self, request, pk):
        pipeline = self.get_object(pk, request.profile.org)
        return Response(CasePipelineSerializer(pipeline).data)

    @extend_schema(
        tags=["Case Pipelines"],
        request=CasePipelineSerializer,
        responses={200: CasePipelineSerializer},
    )
    def put(self, request, pk):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        pipeline = self.get_object(pk, request.profile.org)
        serializer = CasePipelineSerializer(pipeline, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pipeline = serializer.save(updated_by=request.user)
        return Response(CasePipelineSerializer(pipeline).data)

    @extend_schema(tags=["Case Pipelines"], responses={204: None})
    def delete(self, request, pk):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        pipeline = self.get_object(pk, request.profile.org)

        case_count = Case.objects.filter(stage__pipeline=pipeline).count()
        if case_count > 0:
            return Response(
                {
                    "error": f"Cannot delete pipeline with {case_count} cases. Move cases first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        pipeline.is_active = False
        pipeline.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaseStageCreateView(APIView):
    """Create a stage in a pipeline."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Case Stages"],
        request=CaseStageSerializer,
        responses={201: CaseStageSerializer},
    )
    def post(self, request, pipeline_pk):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        org = request.profile.org
        pipeline = get_object_or_404(CasePipeline, pk=pipeline_pk, org=org)

        serializer = CaseStageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage = serializer.save(pipeline=pipeline, org=org, created_by=request.user)
        return Response(CaseStageSerializer(stage).data, status=status.HTTP_201_CREATED)


class CaseStageDetailView(APIView):
    """Update or delete a stage."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Case Stages"],
        request=CaseStageSerializer,
        responses={200: CaseStageSerializer},
    )
    def put(self, request, pk):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        stage = get_object_or_404(CaseStage, pk=pk, org=request.profile.org)
        serializer = CaseStageSerializer(stage, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage = serializer.save(updated_by=request.user)
        return Response(CaseStageSerializer(stage).data)

    @extend_schema(tags=["Case Stages"], responses={204: None})
    def delete(self, request, pk):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        stage = get_object_or_404(CaseStage, pk=pk, org=request.profile.org)

        case_count = stage.cases.count()
        if case_count > 0:
            return Response(
                {
                    "error": f"Cannot delete stage with {case_count} cases. Move cases first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaseStageReorderView(APIView):
    """Bulk reorder stages in a pipeline."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Case Stages"],
        request=inline_serializer(
            name="CaseStageReorderRequest",
            fields={"stage_ids": serializers.ListField(child=serializers.UUIDField())},
        ),
    )
    @transaction.atomic
    def post(self, request, pipeline_pk):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        org = request.profile.org
        pipeline = get_object_or_404(CasePipeline, pk=pipeline_pk, org=org)

        stage_ids = request.data.get("stage_ids", [])

        stages = CaseStage.objects.filter(pipeline=pipeline, id__in=stage_ids)
        if stages.count() != len(stage_ids):
            return Response(
                {"error": "Invalid stage IDs provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for order, stage_id in enumerate(stage_ids):
            CaseStage.objects.filter(id=stage_id).update(order=order)

        return Response({"message": "Stages reordered successfully"})
