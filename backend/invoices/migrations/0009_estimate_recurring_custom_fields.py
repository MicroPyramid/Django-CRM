from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0008_invoice_custom_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="estimate",
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
        migrations.AddField(
            model_name="recurringinvoice",
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
