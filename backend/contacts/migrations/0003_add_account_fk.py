# Migration to add account FK to Contact model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("contacts", "0002_change_phone_to_charfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="account",
            field=models.ForeignKey(
                blank=True,
                help_text="Primary account this contact belongs to",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="primary_contacts",
                to="accounts.account",
            ),
        ),
    ]
