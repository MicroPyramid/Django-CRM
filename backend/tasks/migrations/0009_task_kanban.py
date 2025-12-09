# Generated manually for Task Kanban feature

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def assign_kanban_order(apps, schema_editor):
    """
    Assign initial kanban_order values to existing tasks.
    Group by org and status, order by created_at DESC (newest first).
    """
    Task = apps.get_model("tasks", "Task")

    # Get all unique (org_id, status) combinations
    combinations = Task.objects.values("org_id", "status").distinct()

    for combo in combinations:
        tasks = Task.objects.filter(
            org_id=combo["org_id"], status=combo["status"]
        ).order_by("-created_at")

        for index, task in enumerate(tasks):
            task.kanban_order = (index + 1) * 1000
            task.save(update_fields=["kanban_order"])


def reverse_kanban_order(apps, schema_editor):
    """Reverse: set all kanban_order to 0."""
    Task = apps.get_model("tasks", "Task")
    Task.objects.all().update(kanban_order=0)


class Migration(migrations.Migration):
    # Disable atomic mode to avoid "pending trigger events" error from RLS policies
    atomic = False

    dependencies = [
        ("common", "0012_add_tag_color_description_isactive"),
        ("tasks", "0008_add_enterprise_constraints"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create TaskPipeline model
        migrations.CreateModel(
            name="TaskPipeline",
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
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="Pipeline Name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="Description"),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="If true, new tasks without explicit pipeline go here",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
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
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_pipelines",
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
            ],
            options={
                "verbose_name": "Task Pipeline",
                "verbose_name_plural": "Task Pipelines",
                "db_table": "task_pipeline",
                "ordering": ("-is_default", "name"),
            },
        ),
        # Create TaskStage model
        migrations.CreateModel(
            name="TaskStage",
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
                ("name", models.CharField(max_length=100, verbose_name="Stage Name")),
                ("order", models.PositiveIntegerField(default=0)),
                ("color", models.CharField(default="#6B7280", max_length=7)),
                (
                    "stage_type",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                        ],
                        default="open",
                        max_length=20,
                    ),
                ),
                (
                    "maps_to_status",
                    models.CharField(
                        blank=True,
                        help_text="When task enters this stage, also update Task.status",
                        max_length=50,
                        null=True,
                        verbose_name="Maps to Status",
                    ),
                ),
                (
                    "wip_limit",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Maximum tasks allowed in this stage (null = unlimited)",
                        null=True,
                        verbose_name="WIP Limit",
                    ),
                ),
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
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_stages",
                        to="common.org",
                    ),
                ),
                (
                    "pipeline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stages",
                        to="tasks.taskpipeline",
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
                "verbose_name": "Task Stage",
                "verbose_name_plural": "Task Stages",
                "db_table": "task_stage",
                "ordering": ("order",),
            },
        ),
        # Add kanban_order field to Task
        migrations.AddField(
            model_name="task",
            name="kanban_order",
            field=models.DecimalField(
                decimal_places=6,
                default=0,
                help_text="Order within the kanban column for drag-drop positioning",
                max_digits=15,
                verbose_name="Kanban Order",
            ),
        ),
        # Add stage field to Task
        migrations.AddField(
            model_name="task",
            name="stage",
            field=models.ForeignKey(
                blank=True,
                help_text="Custom pipeline stage (if using pipeline mode)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tasks",
                to="tasks.taskstage",
            ),
        ),
        # Add indexes for kanban queries
        migrations.AddIndex(
            model_name="task",
            index=models.Index(
                fields=["status", "kanban_order"], name="task_status_kanban_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(
                fields=["stage", "kanban_order"], name="task_stage_kanban_idx"
            ),
        ),
        # Add indexes for TaskPipeline
        migrations.AddIndex(
            model_name="taskpipeline",
            index=models.Index(
                fields=["org", "-created_at"], name="task_pipeline_org_idx"
            ),
        ),
        # Add constraint for unique default pipeline per org
        migrations.AddConstraint(
            model_name="taskpipeline",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_default", True)),
                fields=("org",),
                name="unique_default_task_pipeline_per_org",
            ),
        ),
        # Add indexes for TaskStage
        migrations.AddIndex(
            model_name="taskstage",
            index=models.Index(
                fields=["org", "order"], name="task_stage_org_order_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="taskstage",
            index=models.Index(
                fields=["pipeline", "order"], name="task_stage_pipeline_idx"
            ),
        ),
        # Add unique constraint for stage names within pipeline
        migrations.AlterUniqueTogether(
            name="taskstage",
            unique_together={("pipeline", "name")},
        ),
        # Data migration to assign kanban_order to existing tasks
        migrations.RunPython(assign_kanban_order, reverse_kanban_order),
    ]
