from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunity', '0009_salesgoal'),
    ]

    operations = [
        migrations.AddField(
            model_name='opportunity',
            name='custom_fields',
            field=models.JSONField(blank=True, default=dict, help_text='Per-org schema extension; values are validated against common.CustomFieldDefinition.'),
        ),
    ]
