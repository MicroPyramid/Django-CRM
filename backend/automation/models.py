"""Automation rules, a record of each time one ran, and per-action rotation state."""

from django.db import models
from django.db.models import Q

from common.base import BaseOrgModel

ALL = "all"
ANY = "any"
MATCH_MODES = ((ALL, "All"), (ANY, "Any"))

DONE = "done"
FAILED = "failed"
SKIPPED = "skipped"
RUN_STATUSES = ((DONE, "Done"), (FAILED, "Failed"), (SKIPPED, "Skipped"))


class AutomationRule(BaseOrgModel):
    name = models.CharField(max_length=120)
    object_key = models.CharField(max_length=64)
    # {"event": "created" | "updated", "field": str | None, "to": value | None}
    trigger = models.JSONField(default=dict)
    match = models.CharField(max_length=3, choices=MATCH_MODES, default=ALL)
    conditions = models.JSONField(default=list)
    actions = models.JSONField(default=list)
    is_active = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    owner = models.ForeignKey(
        "common.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="automation_rules",
    )
    switched_on_at = models.DateTimeField(null=True, blank=True)
    paused_reason = models.CharField(max_length=32, blank=True, default="")
    last_failure_notice_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "automation_rule"
        ordering = ("position", "created_at")
        # Restated: a subclass Meta replaces BaseOrgModel's, index included.
        indexes = [
            models.Index(fields=["org", "-created_at"]),
            models.Index(fields=["org", "is_active", "object_key", "position"]),
        ]

    def __str__(self):
        return self.name


class AutomationRun(BaseOrgModel):
    rule = models.ForeignKey(
        AutomationRule, on_delete=models.CASCADE, related_name="runs"
    )
    object_key = models.CharField(max_length=64)
    record_id = models.UUIDField()
    record_name = models.CharField(max_length=255)
    status = models.CharField(max_length=8, choices=RUN_STATUSES)
    reason = models.CharField(max_length=255, blank=True, default="")
    chain_id = models.UUIDField()
    depth = models.PositiveSmallIntegerField(default=1)
    triggered_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    # [{"action": int, "type": str, "status": "done" | "undone" | "failed" | "skipped",
    #   "text": str}]; "undone" was applied, then rolled back with its failed rule.
    steps = models.JSONField(default=list)
    skipped_count = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "automation_run"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["org", "-created_at"]),
            models.Index(fields=["rule", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["rule", "window_start"],
                condition=Q(status=SKIPPED),
                name="uniq_automation_skip_window",
            )
        ]

    def __str__(self):
        return f"{self.rule_id} {self.status}"


class AutomationRotation(BaseOrgModel):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE)
    action_index = models.PositiveSmallIntegerField()
    next_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "automation_rotation"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["org", "-created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["rule", "action_index"], name="uniq_automation_rotation"
            )
        ]
