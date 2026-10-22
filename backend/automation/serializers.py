from rest_framework import serializers

from automation.models import AutomationRule, AutomationRun
from automation.validation import validate_rule

# What `validate_rule` reads; a partial update is checked with the rest of the rule.
RULE_KEYS = ("object_key", "trigger", "match", "conditions", "actions")


class RuleSerializer(serializers.ModelSerializer):
    """A rule as an admin edits it. Takes the org as `context["org"]`.

    `org`, `owner`, `switched_on_at`, `paused_reason` and
    `last_failure_notice_at` are set by the server and never read from input.
    """

    owner = serializers.SerializerMethodField()

    class Meta:
        model = AutomationRule
        fields = (
            "id",
            "name",
            "object_key",
            "trigger",
            "match",
            "conditions",
            "actions",
            "is_active",
            "position",
            "owner",
            "switched_on_at",
            "paused_reason",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "switched_on_at",
            "paused_reason",
            "created_at",
            "updated_at",
        )

    def get_owner(self, rule) -> dict | None:
        owner = rule.owner
        if owner is None:
            return None
        return {"id": str(owner.id), "name": owner.user.name}

    def validate(self, attrs):
        # A rule that broke after saving must still be renamed or switched off.
        if (
            self.instance is not None
            and not set(RULE_KEYS) & set(attrs)
            and attrs.get("is_active") is not True
        ):
            return attrs
        current = self.instance or AutomationRule()
        rule = {key: attrs.get(key, getattr(current, key)) for key in RULE_KEYS}
        errors = validate_rule(self.context["org"], rule)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "org": self.context["org"]})


class RunSerializer(serializers.ModelSerializer):
    """One run as the rule's history shows it. Read only."""

    triggered_by = serializers.SerializerMethodField()

    class Meta:
        model = AutomationRun
        fields = (
            "id",
            "created_at",
            "record_id",
            "record_name",
            "object_key",
            "status",
            "reason",
            "steps",
            "skipped_count",
            "depth",
            "triggered_by",
        )
        read_only_fields = fields[:-1]

    def get_triggered_by(self, run) -> dict | None:
        cause = run.triggered_by
        if cause is None:
            return None
        return {"id": str(cause.id), "rule_name": cause.rule.name}
