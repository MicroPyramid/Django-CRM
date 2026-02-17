import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create a default superuser if none exists (for Docker bootstrap)"

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("Superuser already exists — skipping."))
            return

        email = os.environ.get("ADMIN_EMAIL", "admin@localhost")
        password = os.environ.get("ADMIN_PASSWORD", "admin")

        User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Created default superuser: {email}"))
