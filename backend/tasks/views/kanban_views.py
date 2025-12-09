"""
Kanban views for task management.
Supports both status-based (default) and custom pipeline-based kanban boards.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import HasOrgContext
from tasks.models import Task, TaskPipeline, TaskStage
from tasks.serializer import (
    TaskKanbanCardSerializer,
    TaskMoveSerializer,
    TaskPipelineSerializer,
    TaskPipelineListSerializer,
    TaskStageSerializer,
)


class TaskKanbanView(APIView):
    """
    Kanban board view for tasks.

    Supports two modes:
    1. Status-based (default): Groups tasks by Task.status field
    2. Pipeline-based: Groups tasks by TaskStage when pipeline_id is provided
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Tasks Kanban"],
        operation_id="tasks_kanban",
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
                description="Filter by priority (Low/Medium/High)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="search",
                description="Search in title and description",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="due_date__gte",
                description="Due date from",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="due_date__lte",
                description="Due date to",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="account",
                description="Filter by account ID",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="lead",
                description="Filter by lead ID",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="opportunity",
                description="Filter by opportunity ID",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="case",
                description="Filter by case ID",
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
            Task.objects.filter(org=org)
            .select_related(
                "created_by", "stage", "account", "lead", "opportunity", "case"
            )
            .prefetch_related("assigned_to", "tags")
        )

        # Apply permission filtering
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to=request.profile) | Q(created_by=request.profile.user)
            )

        # Apply search/filters
        queryset = self._apply_filters(queryset, request.query_params)

        if pipeline_id:
            # Pipeline-based kanban
            return self._get_pipeline_kanban(queryset, pipeline_id, org)
        else:
            # Status-based kanban
            return self._get_status_kanban(queryset)

    def _apply_filters(self, queryset, params):
        """Apply common filters to queryset."""
        if params.get("assigned_to"):
            queryset = queryset.filter(assigned_to__id=params.get("assigned_to"))
        if params.get("priority"):
            queryset = queryset.filter(priority=params.get("priority"))
        if params.get("search"):
            search = params.get("search")
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        if params.get("due_date__gte"):
            queryset = queryset.filter(due_date__gte=params.get("due_date__gte"))
        if params.get("due_date__lte"):
            queryset = queryset.filter(due_date__lte=params.get("due_date__lte"))
        if params.get("account"):
            queryset = queryset.filter(account_id=params.get("account"))
        if params.get("lead"):
            queryset = queryset.filter(lead_id=params.get("lead"))
        if params.get("opportunity"):
            queryset = queryset.filter(opportunity_id=params.get("opportunity"))
        if params.get("case"):
            queryset = queryset.filter(case_id=params.get("case"))
        if params.get("tags"):
            queryset = queryset.filter(tags__id=params.get("tags"))
        return queryset

    def _get_status_kanban(self, queryset):
        """Build kanban data using Task.status as columns."""
        # Define column order and colors
        status_config = {
            "New": {"order": 1, "color": "#3B82F6", "type": "open"},
            "In Progress": {"order": 2, "color": "#F59E0B", "type": "in_progress"},
            "Completed": {"order": 3, "color": "#22C55E", "type": "completed"},
        }

        columns = []
        for status_value, label in Task.STATUS_CHOICES:
            config = status_config.get(
                status_value, {"order": 99, "color": "#6B7280", "type": "open"}
            )
            tasks = queryset.filter(status=status_value).order_by(
                "kanban_order", "-created_at"
            )

            columns.append(
                {
                    "id": status_value,  # Use status as column ID
                    "name": label,
                    "order": config["order"],
                    "color": config["color"],
                    "stage_type": config["type"],
                    "is_status_column": True,
                    "wip_limit": None,
                    "task_count": tasks.count(),
                    "tasks": TaskKanbanCardSerializer(tasks[:100], many=True).data,
                }
            )

        columns.sort(key=lambda x: x["order"])

        return Response(
            {
                "mode": "status",
                "pipeline": None,
                "columns": columns,
                "total_tasks": queryset.count(),
            }
        )

    def _get_pipeline_kanban(self, queryset, pipeline_id, org):
        """Build kanban data using TaskPipeline stages as columns."""
        pipeline = get_object_or_404(
            TaskPipeline, pk=pipeline_id, org=org, is_active=True
        )

        # Filter tasks to this pipeline
        queryset = queryset.filter(stage__pipeline=pipeline)

        columns = []
        for stage in pipeline.stages.all().order_by("order"):
            tasks = queryset.filter(stage=stage).order_by("kanban_order", "-created_at")

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
                    "task_count": tasks.count(),
                    "tasks": TaskKanbanCardSerializer(tasks[:100], many=True).data,
                }
            )

        return Response(
            {
                "mode": "pipeline",
                "pipeline": TaskPipelineListSerializer(pipeline).data,
                "columns": columns,
                "total_tasks": queryset.count(),
            }
        )


class TaskMoveView(APIView):
    """Move a task to a different stage/status and update order."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Tasks Kanban"],
        operation_id="task_move",
        request=TaskMoveSerializer,
    )
    @transaction.atomic
    def patch(self, request, pk):
        """Move task to different column and/or position."""
        org = request.profile.org
        task = get_object_or_404(Task, pk=pk, org=org)

        # Permission check
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            if not (
                request.profile.user == task.created_by
                or request.profile in task.assigned_to.all()
            ):
                return Response(
                    {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                )

        serializer = TaskMoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Handle stage change
        if "stage_id" in data:
            if data["stage_id"]:
                stage = get_object_or_404(TaskStage, pk=data["stage_id"], org=org)

                # Check WIP limit
                if stage.wip_limit:
                    current_count = stage.tasks.exclude(pk=task.pk).count()
                    if current_count >= stage.wip_limit:
                        return Response(
                            {
                                "error": f"Stage '{stage.name}' has reached its WIP limit of {stage.wip_limit}"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                task.stage = stage

                # Auto-update status if stage has maps_to_status
                if stage.maps_to_status:
                    task.status = stage.maps_to_status
            else:
                task.stage = None

        # Handle status change (for status-based kanban)
        if "status" in data:
            task.status = data["status"]

        # Calculate new order
        new_order = self._calculate_order(data, task, org)
        task.kanban_order = new_order

        task.save()

        return Response(
            {
                "error": False,
                "message": "Task moved successfully",
                "task": TaskKanbanCardSerializer(task).data,
            }
        )

    def _calculate_order(self, data, task, org):
        """Calculate the new kanban_order based on position hints."""
        if "kanban_order" in data:
            return data["kanban_order"]

        above_id = data.get("above_task_id")
        below_id = data.get("below_task_id")

        if above_id and below_id:
            # Insert between two tasks
            above_task = Task.objects.filter(pk=above_id, org=org).first()
            below_task = Task.objects.filter(pk=below_id, org=org).first()
            if above_task and below_task:
                return (above_task.kanban_order + below_task.kanban_order) / 2

        if above_id:
            # Insert after this task
            above_task = Task.objects.filter(pk=above_id, org=org).first()
            if above_task:
                # Find the next task after above_task
                if task.stage:
                    next_task = (
                        Task.objects.filter(
                            org=org,
                            stage=task.stage,
                            kanban_order__gt=above_task.kanban_order,
                        )
                        .order_by("kanban_order")
                        .first()
                    )
                else:
                    next_task = (
                        Task.objects.filter(
                            org=org,
                            status=task.status,
                            stage__isnull=True,
                            kanban_order__gt=above_task.kanban_order,
                        )
                        .order_by("kanban_order")
                        .first()
                    )

                if next_task:
                    return (above_task.kanban_order + next_task.kanban_order) / 2
                return above_task.kanban_order + Decimal("1000")

        if below_id:
            # Insert before this task
            below_task = Task.objects.filter(pk=below_id, org=org).first()
            if below_task:
                return below_task.kanban_order - Decimal("1000")

        # Default: append to end
        if task.stage:
            last_task = (
                Task.objects.filter(stage=task.stage, org=org)
                .exclude(pk=task.pk)
                .order_by("-kanban_order")
                .first()
            )
        else:
            last_task = (
                Task.objects.filter(status=task.status, stage__isnull=True, org=org)
                .exclude(pk=task.pk)
                .order_by("-kanban_order")
                .first()
            )

        if last_task:
            return last_task.kanban_order + Decimal("1000")
        return Decimal("1000")


class TaskPipelineListCreateView(APIView):
    """List and create task pipelines."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Task Pipelines"], responses={200: TaskPipelineListSerializer(many=True)}
    )
    def get(self, request):
        """List all pipelines for the organization."""
        org = request.profile.org
        pipelines = TaskPipeline.objects.filter(org=org, is_active=True)
        serializer = TaskPipelineListSerializer(pipelines, many=True)
        return Response({"pipelines": serializer.data})

    @extend_schema(
        tags=["Task Pipelines"],
        request=TaskPipelineSerializer,
        responses={201: TaskPipelineSerializer},
    )
    def post(self, request):
        """Create a new pipeline."""
        org = request.profile.org

        # Only admins can create pipelines
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Only admins can create pipelines"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TaskPipelineSerializer(data=request.data)
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
                    "name": "To Do",
                    "order": 1,
                    "color": "#3B82F6",
                    "stage_type": "open",
                    "maps_to_status": "New",
                },
                {
                    "name": "In Progress",
                    "order": 2,
                    "color": "#F59E0B",
                    "stage_type": "in_progress",
                    "maps_to_status": "In Progress",
                },
                {
                    "name": "Review",
                    "order": 3,
                    "color": "#8B5CF6",
                    "stage_type": "in_progress",
                    "maps_to_status": "In Progress",
                },
                {
                    "name": "Done",
                    "order": 4,
                    "color": "#22C55E",
                    "stage_type": "completed",
                    "maps_to_status": "Completed",
                },
            ]
            for stage_data in default_stages:
                TaskStage.objects.create(pipeline=pipeline, org=org, **stage_data)

        return Response(
            TaskPipelineSerializer(pipeline).data, status=status.HTTP_201_CREATED
        )


class TaskPipelineDetailView(APIView):
    """Retrieve, update, delete a pipeline."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk, org):
        return get_object_or_404(TaskPipeline, pk=pk, org=org)

    @extend_schema(tags=["Task Pipelines"], responses={200: TaskPipelineSerializer})
    def get(self, request, pk):
        """Get pipeline details with all stages."""
        pipeline = self.get_object(pk, request.profile.org)
        return Response(TaskPipelineSerializer(pipeline).data)

    @extend_schema(
        tags=["Task Pipelines"],
        request=TaskPipelineSerializer,
        responses={200: TaskPipelineSerializer},
    )
    def put(self, request, pk):
        """Update pipeline."""
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        pipeline = self.get_object(pk, request.profile.org)
        serializer = TaskPipelineSerializer(pipeline, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pipeline = serializer.save(updated_by=request.user)
        return Response(TaskPipelineSerializer(pipeline).data)

    @extend_schema(tags=["Task Pipelines"], responses={204: None})
    def delete(self, request, pk):
        """Delete pipeline (soft delete by setting is_active=False)."""
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        pipeline = self.get_object(pk, request.profile.org)

        # Check if pipeline has tasks
        task_count = Task.objects.filter(stage__pipeline=pipeline).count()
        if task_count > 0:
            return Response(
                {
                    "error": f"Cannot delete pipeline with {task_count} tasks. Move tasks first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        pipeline.is_active = False
        pipeline.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskStageCreateView(APIView):
    """Create a stage in a pipeline."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Task Stages"],
        request=TaskStageSerializer,
        responses={201: TaskStageSerializer},
    )
    def post(self, request, pipeline_pk):
        """Add a new stage to pipeline."""
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        org = request.profile.org
        pipeline = get_object_or_404(TaskPipeline, pk=pipeline_pk, org=org)

        serializer = TaskStageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage = serializer.save(pipeline=pipeline, org=org, created_by=request.user)
        return Response(TaskStageSerializer(stage).data, status=status.HTTP_201_CREATED)


class TaskStageDetailView(APIView):
    """Update or delete a stage."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Task Stages"],
        request=TaskStageSerializer,
        responses={200: TaskStageSerializer},
    )
    def put(self, request, pk):
        """Update stage."""
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        stage = get_object_or_404(TaskStage, pk=pk, org=request.profile.org)
        serializer = TaskStageSerializer(stage, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage = serializer.save(updated_by=request.user)
        return Response(TaskStageSerializer(stage).data)

    @extend_schema(tags=["Task Stages"], responses={204: None})
    def delete(self, request, pk):
        """Delete stage."""
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        stage = get_object_or_404(TaskStage, pk=pk, org=request.profile.org)

        # Check if stage has tasks
        task_count = stage.tasks.count()
        if task_count > 0:
            return Response(
                {
                    "error": f"Cannot delete stage with {task_count} tasks. Move tasks first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskStageReorderView(APIView):
    """Bulk reorder stages in a pipeline."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Task Stages"],
        request=inline_serializer(
            name="TaskStageReorderRequest",
            fields={"stage_ids": serializers.ListField(child=serializers.UUIDField())},
        ),
    )
    @transaction.atomic
    def post(self, request, pipeline_pk):
        """Reorder stages by providing ordered list of stage IDs."""
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        org = request.profile.org
        pipeline = get_object_or_404(TaskPipeline, pk=pipeline_pk, org=org)

        stage_ids = request.data.get("stage_ids", [])

        # Validate all stages belong to this pipeline
        stages = TaskStage.objects.filter(pipeline=pipeline, id__in=stage_ids)
        if stages.count() != len(stage_ids):
            return Response(
                {"error": "Invalid stage IDs provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update order
        for order, stage_id in enumerate(stage_ids):
            TaskStage.objects.filter(id=stage_id).update(order=order)

        return Response({"message": "Stages reordered successfully"})
