import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import connection, migrations, models

from common.rls import get_disable_policy_sql, get_enable_policy_sql

# Registered in common/rls/__init__.py:ORG_SCOPED_TABLES. One list here so the
# enable and disable directions cannot drift apart.
AUTOMATION_TABLES = ["automation_rule", "automation_run", "automation_rotation"]


def enable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        for table in AUTOMATION_TABLES:
            cursor.execute(get_enable_policy_sql(table))


def disable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        for table in AUTOMATION_TABLES:
            cursor.execute(get_disable_policy_sql(table))


class Migration(migrations.Migration):
    initial = True

    # RLS policy creation cannot run inside an atomic block.
    atomic = False

    dependencies = [
        ("common", "0054_alter_securityauditlog_event_type"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AutomationRule",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Last Modified At"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("object_key", models.CharField(max_length=64)),
                ("trigger", models.JSONField(default=dict)),
                (
                    "match",
                    models.CharField(
                        choices=[("all", "All"), ("any", "Any")],
                        default="all",
                        max_length=3,
                    ),
                ),
                ("conditions", models.JSONField(default=list)),
                ("actions", models.JSONField(default=list)),
                ("is_active", models.BooleanField(default=False)),
                ("position", models.PositiveIntegerField(default=0)),
                ("switched_on_at", models.DateTimeField(blank=True, null=True)),
                (
                    "paused_reason",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                ("last_failure_notice_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        help_text="Organization this record belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s_set",
                        to="common.org",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="automation_rules",
                        to="common.profile",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
            ],
            options={
                "db_table": "automation_rule",
                "ordering": ("position", "created_at"),
            },
        ),
        migrations.CreateModel(
            name="AutomationRotation",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Last Modified At"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("action_index", models.PositiveSmallIntegerField()),
                ("next_index", models.PositiveIntegerField(default=0)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        help_text="Organization this record belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s_set",
                        to="common.org",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automation.automationrule",
                    ),
                ),
            ],
            options={
                "db_table": "automation_rotation",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="AutomationRun",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Last Modified At"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("object_key", models.CharField(max_length=64)),
                ("record_id", models.UUIDField()),
                ("record_name", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("done", "Done"),
                            ("failed", "Failed"),
                            ("skipped", "Skipped"),
                        ],
                        max_length=8,
                    ),
                ),
                ("reason", models.CharField(blank=True, default="", max_length=255)),
                ("chain_id", models.UUIDField()),
                ("depth", models.PositiveSmallIntegerField(default=1)),
                ("steps", models.JSONField(default=list)),
                ("skipped_count", models.PositiveIntegerField(default=0)),
                ("window_start", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        help_text="Organization this record belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s_set",
                        to="common.org",
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs",
                        to="automation.automationrule",
                    ),
                ),
                (
                    "triggered_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="automation.automationrun",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
            ],
            options={
                "db_table": "automation_run",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="automationrule",
            index=models.Index(
                fields=["org", "-created_at"], name="automation__org_id_d0acd9_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="automationrule",
            index=models.Index(
                fields=["org", "is_active", "object_key", "position"],
                name="automation__org_id_4eb9f4_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="automationrotation",
            index=models.Index(
                fields=["org", "-created_at"], name="automation__org_id_5a1f58_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="automationrotation",
            constraint=models.UniqueConstraint(
                fields=("rule", "action_index"), name="uniq_automation_rotation"
            ),
        ),
        migrations.AddIndex(
            model_name="automationrun",
            index=models.Index(
                fields=["org", "-created_at"], name="automation__org_id_3ac042_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="automationrun",
            index=models.Index(
                fields=["rule", "-created_at"], name="automation__rule_id_429de4_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="automationrun",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "skipped")),
                fields=("rule", "window_start"),
                name="uniq_automation_skip_window",
            ),
        ),
        migrations.RunPython(enable_rls, reverse_code=disable_rls),
    ]
