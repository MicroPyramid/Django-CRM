from django.db.models import Sum
from rest_framework import serializers

from accounts.serializer import AccountSerializer
from cases.approvals import Approval, ApprovalRule
from cases.models import (
    Case,
    CasePipeline,
    CaseStage,
    EmailMessage,
    EscalationPolicy,
    InboundMailbox,
    ReopenPolicy,
    RoutingRule,
    TimeEntry,
)
from common.models import Profile, Teams
from common.utils import STATUS_CHOICE
from common.serializer import (
    OrganizationSerializer,
    ProfileSerializer,
    TagsSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer


# Note: Removed unused serializer property:
# - created_on_arrow (frontend computes its own humanized timestamps)


class CaseSerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    contacts = ContactSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    teams = TeamsSerializer(read_only=True, many=True)
    tags = TagsSerializer(read_only=True, many=True)
    org = OrganizationSerializer()

    first_response_sla_deadline = serializers.DateTimeField(read_only=True)
    resolution_sla_deadline = serializers.DateTimeField(read_only=True)
    is_sla_first_response_breached = serializers.BooleanField(read_only=True)
    is_sla_resolution_breached = serializers.BooleanField(read_only=True)

    # Tier 3 parent/child
    parent_summary = serializers.SerializerMethodField()
    child_count = serializers.SerializerMethodField()

    # Tier 3 time-tracking
    time_summary = serializers.SerializerMethodField()

    def get_parent_summary(self, obj):
        if not obj.parent_id:
            return None
        p = obj.parent
        return {"id": str(p.id), "name": p.name, "status": p.status}

    def get_child_count(self, obj):
        # Prefer prefetched count when callers annotated it.
        if hasattr(obj, "_child_count"):
            return obj._child_count
        return obj.children.count()

    def get_time_summary(self, obj):
        # Only stopped entries contribute to the summary; running timers
        # would otherwise double-count when the user keeps hitting refresh.
        qs = obj.time_entries.filter(ended_at__isnull=False)
        total = qs.aggregate(total=Sum("duration_minutes"))["total"] or 0
        billable = (
            qs.filter(billable=True).aggregate(s=Sum("duration_minutes"))["s"] or 0
        )
        last_entry_at = (
            qs.order_by("-started_at").values_list("started_at", flat=True).first()
        )
        by_profile = []
        rows = (
            qs.values("profile_id", "profile__user__email")
            .annotate(minutes=Sum("duration_minutes"))
            .order_by("-minutes")
        )
        for row in rows:
            by_profile.append(
                {
                    "profile_id": str(row["profile_id"]),
                    "name": row.get("profile__user__email") or "",
                    "minutes": row["minutes"] or 0,
                }
            )
        return {
            "total_minutes": total,
            "billable_minutes": billable,
            "last_entry_at": last_entry_at,
            "by_profile": by_profile,
        }

    class Meta:
        model = Case
        fields = (
            "id",
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "description",
            "created_by",
            "created_at",
            "is_active",
            "account",
            "contacts",
            "teams",
            "assigned_to",
            "tags",
            "org",
            "custom_fields",
            "escalation_count",
            "last_escalation_fired_at",
            # SLA — Tier 2 business-hours-sla
            "sla_first_response_hours",
            "sla_resolution_hours",
            "first_response_at",
            "resolved_at",
            "sla_paused_at",
            "first_response_sla_deadline",
            "resolution_sla_deadline",
            "is_sla_first_response_breached",
            "is_sla_resolution_breached",
            # Tier 3 parent/child
            "parent",
            "is_problem",
            "parent_summary",
            "child_count",
            # Tier 3 time-tracking
            "time_summary",
        )


class CaseCreateSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField(required=False, allow_null=True)
    org = serializers.PrimaryKeyRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org
        # Make account read-only on updates (can only be set on creation)
        if self.instance:
            self.fields["account"].read_only = True

    def validate_name(self, name):
        if self.instance:
            if (
                Case.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Case already exists with this name")

        else:
            if Case.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError("Case already exists with this name")
        return name

    def validate_parent(self, parent):
        # Cross-org link prevention. Cycle/depth/duplicate guards live in
        # Case.clean() and are run when the model save path triggers
        # full_clean(); we still check here so callers get a clear error
        # before save attempts.
        if parent is None:
            return parent
        if parent.org_id != self.org.id:
            raise serializers.ValidationError(
                "Parent case must belong to the same organization."
            )
        if self.instance and parent.id == self.instance.id:
            raise serializers.ValidationError("A case cannot be its own parent.")
        if parent.status == "Duplicate":
            raise serializers.ValidationError(
                "Cannot link to a case that has been merged."
            )
        return parent

    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "description",
            "is_active",
            "account",
            "org",
            "custom_fields",
            "parent",
            "is_problem",
        )
        read_only_fields = ("org",)


class CaseCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "teams",
            "assigned_to",
            "account",
            "contacts",
            "tags",
            "description",
        )


class CaseDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    case_attachment = serializers.FileField()


class CaseCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


# ============================================
# Kanban Serializers
# ============================================


class CaseStageSerializer(serializers.ModelSerializer):
    """Serializer for case stages."""

    case_count = serializers.SerializerMethodField()

    class Meta:
        model = CaseStage
        fields = [
            "id",
            "name",
            "order",
            "color",
            "stage_type",
            "maps_to_status",
            "wip_limit",
            "case_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    def get_case_count(self, obj):
        return obj.cases.count()


class CasePipelineSerializer(serializers.ModelSerializer):
    """Serializer for case pipelines with nested stages."""

    stages = CaseStageSerializer(many=True, read_only=True)
    stage_count = serializers.SerializerMethodField()
    case_count = serializers.SerializerMethodField()

    class Meta:
        model = CasePipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stages",
            "stage_count",
            "case_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    def get_stage_count(self, obj):
        return obj.stages.count()

    def get_case_count(self, obj):
        return Case.objects.filter(stage__pipeline=obj).count()


class CasePipelineListSerializer(serializers.ModelSerializer):
    """Simplified pipeline serializer for lists."""

    stage_count = serializers.SerializerMethodField()
    case_count = serializers.SerializerMethodField()

    class Meta:
        model = CasePipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stage_count",
            "case_count",
            "created_at",
        ]

    def get_stage_count(self, obj):
        return obj.stages.count()

    def get_case_count(self, obj):
        return Case.objects.filter(stage__pipeline=obj).count()


class CaseKanbanCardSerializer(serializers.ModelSerializer):
    """Lightweight serializer for kanban cards (minimal fields for performance)."""

    assigned_to = ProfileSerializer(read_only=True, many=True)
    account_name = serializers.SerializerMethodField()
    is_sla_breached = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            "id",
            "name",
            "status",
            "priority",
            "case_type",
            "stage",
            "kanban_order",
            "account_name",
            "assigned_to",
            "is_sla_breached",
            "is_sla_first_response_breached",
            "is_sla_resolution_breached",
            "escalation_count",
            "last_escalation_fired_at",
            "created_at",
        ]

    def get_account_name(self, obj):
        return obj.account.name if obj.account else None

    def get_is_sla_breached(self, obj):
        """Return True if any SLA is breached."""
        return obj.is_sla_first_response_breached or obj.is_sla_resolution_breached


class ReopenPolicySerializer(serializers.ModelSerializer):
    """Per-org reopen policy. Only non-terminal statuses allowed for reopen_to_status."""

    NON_TERMINAL_STATUSES = ("New", "Assigned", "Pending")

    class Meta:
        model = ReopenPolicy
        fields = (
            "is_enabled",
            "reopen_window_days",
            "reopen_to_status",
            "notify_assigned",
        )

    def validate_reopen_to_status(self, value):
        if value not in self.NON_TERMINAL_STATUSES:
            raise serializers.ValidationError(
                f"reopen_to_status must be one of {self.NON_TERMINAL_STATUSES}"
            )
        return value

    def validate_reopen_window_days(self, value):
        if value < 1 or value > 365:
            raise serializers.ValidationError(
                "reopen_window_days must be between 1 and 365"
            )
        return value


class EscalationPolicySerializer(serializers.ModelSerializer):
    """Per-org, per-priority escalation policy. See docs/cases/tier1/escalation.md."""

    first_response_target = ProfileSerializer(read_only=True)
    resolution_target = ProfileSerializer(read_only=True)
    notify_team = TeamsSerializer(read_only=True)
    # `*_id` write-only relational fields are scoped to the request's org in
    # __init__ (a class-level queryset would leak cross-tenant rows in the
    # browsable API). DRF requires a non-None placeholder here.
    first_response_target_id = serializers.PrimaryKeyRelatedField(
        source="first_response_target",
        queryset=Profile.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    resolution_target_id = serializers.PrimaryKeyRelatedField(
        source="resolution_target",
        queryset=Profile.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    notify_team_id = serializers.PrimaryKeyRelatedField(
        source="notify_team",
        queryset=Teams.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = EscalationPolicy
        fields = (
            "id",
            "priority",
            "first_response_action",
            "resolution_action",
            "first_response_target",
            "resolution_target",
            "notify_team",
            "first_response_target_id",
            "resolution_target_id",
            "notify_team_id",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request") if hasattr(self, "context") else None
        org = getattr(getattr(request, "profile", None), "org", None) if request else None
        if org is None:
            org = self.context.get("org") if hasattr(self, "context") else None
        if org is not None:
            self.fields["first_response_target_id"].queryset = Profile.objects.filter(
                org=org
            )
            self.fields["resolution_target_id"].queryset = Profile.objects.filter(
                org=org
            )
            self.fields["notify_team_id"].queryset = Teams.objects.filter(org=org)

    def validate(self, attrs):
        priority = attrs.get("priority", getattr(self.instance, "priority", None))
        if self.instance is None and priority is not None:
            org = self.context.get("org")
            if org and EscalationPolicy.objects.filter(org=org, priority=priority).exists():
                raise serializers.ValidationError(
                    {"priority": f"Policy already exists for priority {priority}."}
                )
        return attrs


class InboundMailboxSerializer(serializers.ModelSerializer):
    """Per-org inbound mailbox config. See docs/cases/tier1/email-to-ticket.md."""

    default_assignee = ProfileSerializer(read_only=True)
    default_assignee_id = serializers.PrimaryKeyRelatedField(
        source="default_assignee",
        queryset=Profile.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = InboundMailbox
        fields = (
            "id",
            "address",
            "provider",
            "webhook_secret",
            "default_priority",
            "default_case_type",
            "default_assignee",
            "default_assignee_id",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request") if hasattr(self, "context") else None
        org = (
            getattr(getattr(request, "profile", None), "org", None) if request else None
        )
        if org is None:
            org = self.context.get("org") if hasattr(self, "context") else None
        if org is not None:
            self.fields["default_assignee_id"].queryset = Profile.objects.filter(
                org=org
            )

    def validate_address(self, value):
        # Postgres unique constraint already enforces (org, address); this is a
        # nicer error than IntegrityError on the create path.
        org = self.context.get("org")
        if org and self.instance is None:
            if InboundMailbox.objects.filter(org=org, address__iexact=value).exists():
                raise serializers.ValidationError(
                    f"A mailbox with address {value!r} already exists for this org."
                )
        return value


class EmailMessageSerializer(serializers.ModelSerializer):
    """Read-only view of an EmailMessage row, used by the case-detail feed."""

    class Meta:
        model = EmailMessage
        fields = (
            "id",
            "case",
            "direction",
            "message_id",
            "in_reply_to",
            "from_address",
            "to_addresses",
            "cc_addresses",
            "subject",
            "body_text",
            "body_html",
            "received_at",
            "drop_reason",
            "created_at",
        )
        read_only_fields = fields


class RoutingRuleSerializer(serializers.ModelSerializer):
    """Per-org auto-routing rule. See docs/cases/tier1/auto-routing.md."""

    target_assignees = ProfileSerializer(read_only=True, many=True)
    target_team = TeamsSerializer(read_only=True)
    target_assignee_ids = serializers.PrimaryKeyRelatedField(
        source="target_assignees",
        queryset=Profile.objects.none(),
        write_only=True,
        required=False,
        many=True,
    )
    target_team_id = serializers.PrimaryKeyRelatedField(
        source="target_team",
        queryset=Teams.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = RoutingRule
        fields = (
            "id",
            "name",
            "priority_order",
            "is_active",
            "conditions",
            "strategy",
            "stop_processing",
            "target_assignees",
            "target_team",
            "target_assignee_ids",
            "target_team_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    SUPPORTED_OPS = ("eq", "in", "contains", "regex")
    SUPPORTED_FIELDS = (
        "priority",
        "case_type",
        "account",
        "tags",
        "from_email_domain",
        "mailbox_id",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request") if hasattr(self, "context") else None
        org = (
            getattr(getattr(request, "profile", None), "org", None)
            if request
            else None
        )
        if org is None:
            org = self.context.get("org") if hasattr(self, "context") else None
        if org is not None:
            self.fields["target_assignee_ids"].child_relation.queryset = (
                Profile.objects.filter(org=org)
            )
            self.fields["target_team_id"].queryset = Teams.objects.filter(org=org)

    def validate_conditions(self, value):
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("conditions must be a list of objects.")
        for i, cond in enumerate(value):
            if not isinstance(cond, dict):
                raise serializers.ValidationError(
                    f"conditions[{i}] must be an object."
                )
            field = cond.get("field")
            op = cond.get("op", "eq")
            if not isinstance(field, str) or not field:
                raise serializers.ValidationError(
                    f"conditions[{i}].field is required."
                )
            if not (
                field in self.SUPPORTED_FIELDS or field.startswith("custom_fields.")
            ):
                raise serializers.ValidationError(
                    f"conditions[{i}].field {field!r} is not supported."
                )
            if op not in self.SUPPORTED_OPS:
                raise serializers.ValidationError(
                    f"conditions[{i}].op {op!r} is not supported."
                )
            if "value" not in cond:
                raise serializers.ValidationError(
                    f"conditions[{i}].value is required."
                )
        return value

    def validate(self, attrs):
        strategy = attrs.get("strategy", getattr(self.instance, "strategy", "direct"))
        if strategy == "by_team":
            target_team = attrs.get(
                "target_team", getattr(self.instance, "target_team", None)
            )
            if target_team is None:
                raise serializers.ValidationError(
                    {"target_team_id": "by_team strategy requires target_team_id."}
                )
        if strategy in ("round_robin", "least_busy", "direct"):
            assignees = attrs.get("target_assignees")
            if assignees is None and self.instance is None:
                raise serializers.ValidationError(
                    {
                        "target_assignee_ids": (
                            f"{strategy} strategy requires at least one target assignee."
                        )
                    }
                )
        return attrs


class TimeEntrySerializer(serializers.ModelSerializer):
    """Read shape for time entries. See docs/cases/tier3/time-tracking.md."""

    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = TimeEntry
        fields = (
            "id",
            "case",
            "profile",
            "started_at",
            "ended_at",
            "duration_minutes",
            "description",
            "billable",
            "hourly_rate",
            "currency",
            "invoice",
            "auto_stopped",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "duration_minutes",
            "auto_stopped",
            "invoice",
            "created_at",
            "updated_at",
        )


class TimeEntryCreateSerializer(serializers.ModelSerializer):
    """Manual time entry creation (POST /api/cases/<pk>/time-entries/).

    `case`, `profile`, and `org` are injected by the view and not accepted
    from the client. Validation rejects negative durations and negative
    hourly rates so the DB CheckConstraint is a backstop, not the first
    line of defense.
    """

    class Meta:
        model = TimeEntry
        fields = (
            "started_at",
            "ended_at",
            "description",
            "billable",
            "hourly_rate",
            "currency",
        )

    def validate_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Description is required when logging time manually."
            )
        return value.strip()

    def validate(self, attrs):
        started = attrs.get("started_at")
        ended = attrs.get("ended_at")
        if started and ended and ended < started:
            raise serializers.ValidationError(
                {"ended_at": "ended_at must be on or after started_at."}
            )
        rate = attrs.get("hourly_rate")
        if rate is not None and rate < 0:
            raise serializers.ValidationError(
                {"hourly_rate": "hourly_rate cannot be negative."}
            )
        return attrs


class TimeEntryUpdateSerializer(serializers.ModelSerializer):
    """Update path for /api/time-entries/<pk>/.

    Lets the owner (or an admin) revise the start/end window, description,
    billable flag, and hourly rate. `case`, `profile`, and `invoice` stay
    read-only — moving an entry between cases or stealing someone else's
    timer is intentionally not supported.
    """

    class Meta:
        model = TimeEntry
        fields = (
            "started_at",
            "ended_at",
            "description",
            "billable",
            "hourly_rate",
            "currency",
        )

    def validate_description(self, value):
        # Only blocks explicit attempts to clear the field; PATCH bodies that
        # omit `description` (e.g., toggling billable) skip this entirely.
        if value is not None and not value.strip():
            raise serializers.ValidationError(
                "Description cannot be empty."
            )
        return value.strip() if value else value

    def validate(self, attrs):
        started = attrs.get(
            "started_at", self.instance.started_at if self.instance else None
        )
        ended = attrs.get(
            "ended_at", self.instance.ended_at if self.instance else None
        )
        if started and ended and ended < started:
            raise serializers.ValidationError(
                {"ended_at": "ended_at must be on or after started_at."}
            )
        rate = attrs.get("hourly_rate")
        if rate is not None and rate < 0:
            raise serializers.ValidationError(
                {"hourly_rate": "hourly_rate cannot be negative."}
            )
        return attrs


class CaseMoveSerializer(serializers.Serializer):
    """Serializer for moving cases in kanban."""

    stage_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=STATUS_CHOICE, required=False)
    kanban_order = serializers.DecimalField(
        max_digits=15, decimal_places=6, required=False
    )
    above_case_id = serializers.UUIDField(required=False, allow_null=True)
    below_case_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get("stage_id") and not attrs.get("status"):
            raise serializers.ValidationError(
                "Either stage_id or status must be provided"
            )
        return attrs


# ---------------------------------------------------------------------------
# Tier 3 approval workflows


class ApprovalRuleSerializer(serializers.ModelSerializer):
    """Read + write serializer for admin rule CRUD.

    The approver pool is a list of profile IDs on writes; on reads we expose
    a thin {id, email} per-approver shape so the admin UI can render names
    without an N+1 fetch.
    """

    approver_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        required=False,
        source="approvers",
        queryset=Approval._meta.get_field("requested_by").related_model.objects.all(),
    )
    approvers = serializers.SerializerMethodField()
    match_team_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        allow_null=True,
        source="match_team",
        queryset=Teams.objects.all(),
    )
    match_team = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRule
        fields = (
            "id",
            "name",
            "trigger_event",
            "match_priority",
            "match_case_type",
            "match_team",
            "match_team_id",
            "approver_role",
            "approvers",
            "approver_ids",
            "is_active",
            "created_at",
            "updated_at",
        )

    def get_approvers(self, obj):
        return [
            {"id": str(p.id), "email": getattr(p.user, "email", "") or ""}
            for p in obj.approvers.all().select_related("user")
        ]

    def get_match_team(self, obj):
        if not obj.match_team_id:
            return None
        return {"id": str(obj.match_team_id), "name": obj.match_team.name}


class ApprovalSerializer(serializers.ModelSerializer):
    """Read serializer used by the inbox + case pane."""

    case_summary = serializers.SerializerMethodField()
    rule_summary = serializers.SerializerMethodField()
    requested_by = serializers.SerializerMethodField()
    approver = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = (
            "id",
            "state",
            "note",
            "reason",
            "decided_at",
            "case_summary",
            "rule_summary",
            "requested_by",
            "approver",
            "created_at",
            "updated_at",
        )

    def get_case_summary(self, obj):
        c = obj.case
        return {
            "id": str(c.id),
            "name": c.name,
            "status": c.status,
            "priority": c.priority,
        }

    def get_rule_summary(self, obj):
        r = obj.rule
        return {
            "id": str(r.id),
            "name": r.name,
            "trigger_event": r.trigger_event,
            "approver_role": r.approver_role,
        }

    def _profile_label(self, profile):
        if profile is None:
            return None
        email = getattr(profile.user, "email", "") if profile.user_id else ""
        return {"id": str(profile.id), "email": email or ""}

    def get_requested_by(self, obj):
        return self._profile_label(obj.requested_by)

    def get_approver(self, obj):
        return self._profile_label(obj.approver)


class ApprovalRequestSerializer(serializers.Serializer):
    """Body shape for ``POST /api/cases/<pk>/request-approval/``."""

    rule_id = serializers.UUIDField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, default="")
