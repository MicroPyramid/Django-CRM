from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0024_alter_customfielddefinition_target_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="magiclinktoken",
            name="delivery",
            field=models.CharField(
                choices=[("link", "Link"), ("code", "Code")],
                default="link",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="magiclinktoken",
            name="code_hash",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
        migrations.AddField(
            model_name="magiclinktoken",
            name="attempts",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
