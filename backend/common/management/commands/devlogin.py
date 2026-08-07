"""Mint a JWT for a given user. Local-dev only.

Refuses to run unless DEBUG is true so this can never produce a token in
a production environment.
"""

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from common.models import Org, Profile
from common.serializer import OrgAwareRefreshToken

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Mint a JWT access/refresh pair for a user (local development only). "
        "Refuses to run unless settings.DEBUG is true."
    )

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email of the user to mint a token for")
        parser.add_argument(
            "--org",
            help=(
                "Optional org name or UUID. If supplied, the token is bound to "
                "this org (skips the post-login org-switch step)."
            ),
        )
        parser.add_argument(
            "--create",
            action="store_true",
            help="Create the user if it doesn't exist (with a random password).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "devlogin refuses to run when DEBUG=False. This command is for "
                "local development only."
            )

        email = options["email"]
        org_arg = options["org"]
        create = options["create"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            if not create:
                raise CommandError(
                    f"No user with email {email!r}. Re-run with --create to make one."
                )
            user = User.objects.create(
                email=email,
                password=make_password(secrets.token_urlsafe(32)),
            )
            self.stdout.write(self.style.SUCCESS(f"Created user {email}"))

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        org = None
        profile = None
        if org_arg:
            org = self._resolve_org(org_arg)
            try:
                profile = Profile.objects.get(user=user, org=org, is_active=True)
            except Profile.DoesNotExist:
                raise CommandError(
                    f"User {email!r} has no active profile in org "
                    f"{org.name!r} ({org.id})."
                )

        token = OrgAwareRefreshToken.for_user_and_org(user, org, profile)
        access = str(token.access_token)
        refresh = str(token)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Tokens ==="))
        self.stdout.write(f"access_token:  {access}")
        self.stdout.write(f"refresh_token: {refresh}")
        if org:
            self.stdout.write(f"bound to org:  {org.name} ({org.id})")
        else:
            # `/api/auth/orgswitch/` was printed here and resolves to nothing.
            # The route is `auth/switch-org/` (`common/urls.py`, name
            # `switch_org`), and in practice you do not call it by hand: a
            # token with no org claim lands you on `/org` to pick one.
            self.stdout.write(
                "bound to org:  (none. You will land on /org to pick one, "
                "which POSTs /api/auth/switch-org/)"
            )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Paste into browser devtools ==="))
        # Cookies, not localStorage. `frontend/src/hooks.server.js` reads
        # `jwt_access`, `jwt_refresh` and `org` off the request cookies and
        # redirects to /login when they are absent; nothing server-side can
        # see localStorage, so the snippet this used to print looked like it
        # worked and left you on the login page. The httpOnly flag the app
        # sets on its own cookies is a write-side attribute, so a plain
        # `document.cookie` value of the same name is read back identically.
        one_year = 60 * 60 * 24 * 365
        lines = [
            f"const y = {one_year};",
            f"document.cookie = `jwt_access={access}; path=/; max-age=${{y}}; samesite=lax`;",
            f"document.cookie = `jwt_refresh={refresh}; path=/; max-age=${{y}}; samesite=lax`;",
        ]
        if org:
            lines.append(
                f"document.cookie = `org={org.id}; path=/; max-age=${{y}}; samesite=lax`;"
            )
        else:
            # Without an org claim the shell sends you to /org to pick one, so
            # setting an `org` cookie here would contradict the token.
            lines.append("// no --org, so you will land on /org to pick one")
        lines.append("location.reload();")
        self.stdout.write("\n".join(lines))

    def _resolve_org(self, org_arg: str) -> Org:
        from django.core.exceptions import ValidationError

        try:
            return Org.objects.get(id=org_arg)
        except (Org.DoesNotExist, ValueError, ValidationError):
            pass
        matches = list(Org.objects.filter(name=org_arg))
        if not matches:
            raise CommandError(f"No org found matching {org_arg!r}.")
        if len(matches) > 1:
            ids = ", ".join(str(o.id) for o in matches)
            raise CommandError(
                f"Multiple orgs named {org_arg!r}; pass an id instead: {ids}"
            )
        return matches[0]
