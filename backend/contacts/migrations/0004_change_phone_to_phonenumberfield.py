# Migration to change Contact.phone field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contacts", "0003_add_account_fk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                verbose_name="Phone",
            ),
        ),
    ]
