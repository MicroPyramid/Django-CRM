from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0019_csatsurvey"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="children",
                to="cases.case",
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="is_problem",
            field=models.BooleanField(
                default=False,
                help_text="Marks this case as an ITIL 'problem' (umbrella ticket).",
            ),
        ),
        migrations.AddIndex(
            model_name="case",
            index=models.Index(fields=["parent"], name="case_parent_idx"),
        ),
    ]
