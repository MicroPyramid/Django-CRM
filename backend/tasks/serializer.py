from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    ProfileSerializer,
    TagsSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer
from tasks.models import (
    Board,
    BoardColumn,
    BoardMember,
    BoardTask,
    Task,
    TaskPipeline,
    TaskStage,
)


class BoardMemberSerializer(serializers.ModelSerializer):
    """Serializer for board members"""

    profile = ProfileSerializer(read_only=True)
    profile_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = BoardMember
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "board")


class BoardTaskSerializer(serializers.ModelSerializer):
    """Serializer for board tasks"""

    assigned_to = ProfileSerializer(many=True, read_only=True)
    assigned_to_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    is_completed = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = BoardTask
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "completed_at")


class BoardColumnSerializer(serializers.ModelSerializer):
    """Serializer for board columns"""

    tasks = BoardTaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = BoardColumn
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "board")

    @extend_schema_field(int)
    def get_task_count(self, obj):
        return obj.tasks.count()


class BoardColumnListSerializer(serializers.ModelSerializer):
    """Simplified column serializer for lists"""

    task_count = serializers.SerializerMethodField()

    class Meta:
        model = BoardColumn
        fields = ["id", "name", "order", "color", "limit", "task_count"]

    @extend_schema_field(int)
    def get_task_count(self, obj):
        return obj.tasks.count()


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for boards"""

    owner = ProfileSerializer(read_only=True)
    columns = BoardColumnListSerializer(many=True, read_only=True)
    members = BoardMemberSerializer(source="memberships", many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "owner",
            "org",
        )

    @extend_schema_field(int)
    def get_member_count(self, obj):
        return obj.members.count()

    @extend_schema_field(int)
    def get_task_count(self, obj):
        return BoardTask.objects.filter(column__board=obj).count()


class BoardListSerializer(serializers.ModelSerializer):
    """Simplified board serializer for lists"""

    owner = ProfileSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    column_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "is_archived",
            "member_count",
            "column_count",
            "task_count",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(int)
    def get_member_count(self, obj):
        return obj.members.count()

    @extend_schema_field(int)
    def get_column_count(self, obj):
        return obj.columns.count()

    @extend_schema_field(int)
    def get_task_count(self, obj):
        return BoardTask.objects.filter(column__board=obj).count()


class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    tags = TagsSerializer(read_only=True, many=True)
    task_attachment = AttachmentsSerializer(read_only=True, many=True)
    task_comments = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "priority",
            "due_date",
            "description",
            "account",
            "opportunity",
            "case",
            "lead",
            "created_by",
            "created_at",
            "contacts",
            "teams",
            "assigned_to",
            "tags",
            "task_attachment",
            "task_comments",
        )


class TaskCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

        self.fields["title"].required = True

    def validate_title(self, title):
        if self.instance:
            if (
                Task.objects.filter(title__iexact=title, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Task already exists with this title")
        else:
            if Task.objects.filter(title__iexact=title, org=self.org).exists():
                raise serializers.ValidationError("Task already exists with this title")
        return title

    def validate(self, attrs):
        """Validate that task has at most one parent entity."""
        attrs = super().validate(attrs)
        parent_fields = ["account", "opportunity", "case", "lead"]
        set_parents = [field for field in parent_fields if attrs.get(field)]
        if len(set_parents) > 1:
            raise serializers.ValidationError(
                {
                    "account": (
                        "A task can only be linked to one parent entity "
                        f"(Account, Opportunity, Case, or Lead). "
                        f"Currently set: {', '.join(set_parents)}"
                    )
                }
            )
        return attrs

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "priority",
            "due_date",
            "description",
            "account",
            "opportunity",
            "case",
            "lead",
            "created_by",
            "created_at",
        )


class TaskDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    task_attachment = serializers.FileField()


class TaskCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


class TaskCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            "title",
            "status",
            "priority",
            "due_date",
            "description",
            "account",
            "opportunity",
            "case",
            "lead",
            "contacts",
            "teams",
            "assigned_to",
            "tags",
        )


# ============================================================================
# Kanban Serializers
# ============================================================================


class TaskStageSerializer(serializers.ModelSerializer):
    """Serializer for task stages."""

    task_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskStage
        fields = [
            "id",
            "name",
            "order",
            "color",
            "stage_type",
            "maps_to_status",
            "wip_limit",
            "task_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    @extend_schema_field(int)
    def get_task_count(self, obj):
        return obj.tasks.count()


class TaskPipelineSerializer(serializers.ModelSerializer):
    """Serializer for task pipelines with nested stages."""

    stages = TaskStageSerializer(many=True, read_only=True)
    stage_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskPipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stages",
            "stage_count",
            "task_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    @extend_schema_field(int)
    def get_stage_count(self, obj):
        return obj.stages.count()

    @extend_schema_field(int)
    def get_task_count(self, obj):
        return Task.objects.filter(stage__pipeline=obj).count()


class TaskPipelineListSerializer(serializers.ModelSerializer):
    """Simplified pipeline serializer for lists."""

    stage_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskPipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stage_count",
            "task_count",
            "created_at",
        ]

    @extend_schema_field(int)
    def get_stage_count(self, obj):
        return obj.stages.count()

    @extend_schema_field(int)
    def get_task_count(self, obj):
        return Task.objects.filter(stage__pipeline=obj).count()


class RelatedEntitySerializer(serializers.Serializer):
    """Minimal serializer for related entities on kanban cards."""

    id = serializers.UUIDField()
    name = serializers.CharField()


class TaskKanbanCardSerializer(serializers.ModelSerializer):
    """Lightweight serializer for kanban cards (minimal fields for performance)."""

    assigned_to = ProfileSerializer(read_only=True, many=True)
    is_overdue = serializers.BooleanField(read_only=True)
    related_entity = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "status",
            "priority",
            "due_date",
            "is_overdue",
            "stage",
            "kanban_order",
            "assigned_to",
            "related_entity",
            "created_at",
        ]

    @extend_schema_field(RelatedEntitySerializer(allow_null=True))
    def get_related_entity(self, obj):
        """Return the related entity (account, lead, opportunity, or case) if any."""
        if obj.account_id:
            return {"id": obj.account_id, "name": obj.account.name, "type": "account"}
        if obj.lead_id:
            return {"id": obj.lead_id, "name": str(obj.lead), "type": "lead"}
        if obj.opportunity_id:
            return {
                "id": obj.opportunity_id,
                "name": obj.opportunity.name,
                "type": "opportunity",
            }
        if obj.case_id:
            return {"id": obj.case_id, "name": obj.case.name, "type": "case"}
        return None


class TaskMoveSerializer(serializers.Serializer):
    """Serializer for moving tasks in kanban."""

    stage_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES, required=False)
    kanban_order = serializers.DecimalField(
        max_digits=15, decimal_places=6, required=False
    )
    above_task_id = serializers.UUIDField(required=False, allow_null=True)
    below_task_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        # Must provide either stage_id or status
        if not attrs.get("stage_id") and not attrs.get("status"):
            raise serializers.ValidationError(
                "Either stage_id or status must be provided"
            )
        return attrs
