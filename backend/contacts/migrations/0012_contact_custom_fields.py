from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0011_inbound_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='custom_fields',
            field=models.JSONField(blank=True, default=dict, help_text='Per-org schema extension; values are validated against common.CustomFieldDefinition.'),
        ),
    ]
