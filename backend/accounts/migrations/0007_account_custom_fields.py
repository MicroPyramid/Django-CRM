from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_add_enterprise_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='custom_fields',
            field=models.JSONField(blank=True, default=dict, help_text='Per-org schema extension; values are validated against common.CustomFieldDefinition.'),
        ),
    ]
