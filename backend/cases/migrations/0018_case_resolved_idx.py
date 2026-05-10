# Resolution-window scans for MTTR / SLA breach aggregations — see
# docs/cases/tier2/reporting.md "Data model changes". The existing
# (org, -created_at) index doesn't cover queries that filter by resolved_at.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0017_sla_pause"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="case",
            index=models.Index(
                fields=["org", "resolved_at"], name="case_org_resolved_idx"
            ),
        ),
    ]
