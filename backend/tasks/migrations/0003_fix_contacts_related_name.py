# Migration to fix Task.contacts related_name

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0002_add_opportunity_case_lead_fks"),
        ("contacts", "0004_change_phone_to_phonenumberfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="contacts",
            field=models.ManyToManyField(
                related_name="task_contacts",
                to="contacts.contact",
            ),
        ),
    ]
