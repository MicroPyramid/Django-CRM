from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0020_org_csat_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="org",
            name="auto_close_children_on_parent_close",
            field=models.BooleanField(default=False),
        ),
    ]
