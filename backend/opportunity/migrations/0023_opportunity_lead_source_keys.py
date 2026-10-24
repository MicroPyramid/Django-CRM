from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("opportunity", "0022_add_zar_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="opportunity",
            name="lead_source",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Lead Source"
            ),
        ),
        migrations.AddField(
            model_name="opportunity",
            name="source_detail",
            field=models.CharField(
                blank=True, default="", max_length=100, verbose_name="Sub-source"
            ),
        ),
        migrations.AddField(
            model_name="opportunity",
            name="source_ref",
            field=models.CharField(
                blank=True, default="", max_length=255, verbose_name="Reference"
            ),
        ),
    ]
