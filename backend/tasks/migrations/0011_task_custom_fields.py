from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0010_rename_task_status_kanban_idx_task_status_e6f973_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="custom_fields",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Per-org schema extension; values are validated against common.CustomFieldDefinition.",
            ),
        ),
    ]
