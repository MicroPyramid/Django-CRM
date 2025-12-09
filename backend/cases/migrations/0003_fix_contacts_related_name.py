# Migration to add explicit related_name to Case.contacts

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0002_initial"),
        ("contacts", "0004_change_phone_to_phonenumberfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="contacts",
            field=models.ManyToManyField(
                related_name="case_contacts",
                to="contacts.contact",
            ),
        ),
    ]
