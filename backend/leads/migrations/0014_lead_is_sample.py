from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0013_lead_custom_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="is_sample",
            field=models.BooleanField(
                default=False,
                help_text="True only for demo rows created by common.packs.applier._apply_sample_data. Server-set exclusively, never expose this as a writable field on any serializer. It is the sole key common.packs.applier.clear_sample_data uses to decide what to delete, so a client-writable path here would let a user mark an arbitrary real lead as sample and have it deleted.",
            ),
        ),
    ]
