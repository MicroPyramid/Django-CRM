# Composite index used by the cases analytics aggregation queries — see
# docs/cases/tier2/reporting.md "Data model changes". Lets us scan
# `Case` Activity rows by (entity_type, action, created_at) inside a single
# org without re-walking the whole table.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0018_add_notification"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="activity",
            index=models.Index(
                fields=["org", "entity_type", "action", "created_at"],
                name="activity_analytics_idx",
            ),
        ),
    ]
