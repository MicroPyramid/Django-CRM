from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0007_add_cancelled_at_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="custom_fields",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Per-org schema extension; values are validated against "
                    "common.CustomFieldDefinition."
                ),
            ),
        ),
    ]
