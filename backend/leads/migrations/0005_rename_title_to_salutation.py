# Migration to rename title -> salutation and contact_title -> job_title

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0004_remove_company_model"),
    ]

    operations = [
        # Rename title to salutation
        migrations.RenameField(
            model_name="lead",
            old_name="title",
            new_name="salutation",
        ),
        # Rename contact_title to job_title
        migrations.RenameField(
            model_name="lead",
            old_name="contact_title",
            new_name="job_title",
        ),
        # Update salutation field attributes (make it nullable since it's no longer required)
        migrations.AlterField(
            model_name="lead",
            name="salutation",
            field=models.CharField(
                blank=True,
                help_text="e.g., Mr, Mrs, Ms, Dr",
                max_length=64,
                null=True,
                verbose_name="Salutation",
            ),
        ),
    ]
