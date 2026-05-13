from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0012_lead_kanban_pipeline'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='custom_fields',
            field=models.JSONField(blank=True, default=dict, help_text='Per-org schema extension; values are validated against common.CustomFieldDefinition.'),
        ),
    ]
