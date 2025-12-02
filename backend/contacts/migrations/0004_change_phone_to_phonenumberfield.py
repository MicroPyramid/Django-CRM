# Migration to change Contact.phone from CharField to PhoneNumberField

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0003_add_account_fk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True,
                max_length=128,
                null=True,
                region=None,
                verbose_name="Phone",
            ),
        ),
    ]
