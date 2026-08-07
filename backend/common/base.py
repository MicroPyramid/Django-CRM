import uuid

# Third party imports
from crum import get_current_user

# Django imports
from django.db import models

# Module imports
from common.mixins import AuditModel

# Help text shared by every `is_sample` column. One string, because the rule it
# states is a security invariant rather than documentation: the flag is the sole
# key `clear_sample_data` deletes on, so any serializer that made it writable
# would let a user mark a real record as sample and have it destroyed. Stating
# that once, next to the definition all six models import, is what stops the
# sixth copy from quietly dropping the warning.
SAMPLE_DATA_HELP_TEXT = (
    "True only for demo rows created by common.packs.applier._apply_sample_data. "
    "Server-set exclusively, never expose this as a writable field on any "
    "serializer. It is the sole key common.packs.applier.clear_sample_data uses "
    "to decide what to delete, so a client-writable path here would let a user "
    "mark an arbitrary real record as sample and have it deleted."
)


class AssignableMixin(models.Model):
    """
    Mixin for models that have assigned_to (Profile) and teams (Teams) fields.

    Provides helper methods for getting users from teams and assignments.
    Models using this mixin must define:
        - assigned_to = ManyToManyField(Profile, ...)
        - teams = ManyToManyField(Teams, ...)
    """

    class Meta:
        abstract = True

    @property
    def get_team_users(self):
        """Get all users who are members of assigned teams."""
        from common.models import Profile

        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        return Profile.objects.filter(id__in=team_user_ids)

    @property
    def get_team_and_assigned_users(self):
        """Get all users from both teams and direct assignments."""
        from common.models import Profile

        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = team_user_ids + assigned_user_ids
        return Profile.objects.filter(id__in=user_ids)

    @property
    def get_assigned_users_not_in_teams(self):
        """Get users who are directly assigned but not part of any assigned team."""
        from common.models import Profile

        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = set(assigned_user_ids) - set(team_user_ids)
        return Profile.objects.filter(id__in=list(user_ids))


class BaseModel(AuditModel):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True, primary_key=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Stamp the audit columns from the request user, when there is one.

        `crum.get_current_user` reads a thread local that only the request
        middleware fills, so it is None in a Celery worker, a management
        command, the shell and a data migration. The previous version answered
        that case by assigning None to both columns, which did two things it did
        not mean to:

        * it discarded a `created_by=` the caller had passed explicitly, and the
          callers with no request are exactly the ones that have to say who to
          credit. `create_invoice_history` passes `created_by=invoice.created_by`
          and `updated_by=updated_by` from a task, so the invoice audit trail,
          whose entire job is recording who changed an invoice, recorded nobody;
        * on an UPDATE it assigned None to `created_by` as well, so any save
          from a worker permanently erased an existing row's creator. The
          in-request branch below is careful not to touch `created_by` on
          update; the no-request branch overwrote it every time.

        With a request user present the behaviour is deliberately unchanged: the
        request user wins over anything in the payload. Fifteen serializers still
        leave `created_by` or `updated_by` writable, and this assignment is what
        makes a forged value harmless. Loosening it here would turn that latent
        mass-assignment into a live one, so the two cases stay separate: inside a
        request the server decides, outside one the caller does, and outside a
        request there is no client to decide against.
        """
        user = get_current_user()
        if user is None or user.is_anonymous:
            # No request, so nothing to derive from. Leave whatever the caller
            # set, which is None for anyone who set nothing.
            super().save(*args, **kwargs)
            return
        if self._state.adding:
            self.created_by = user
        # On update `created_by` is left alone: it records who made the row, not
        # who last touched it.
        self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id)


class OrgScopedQuerySet(models.QuerySet):
    """QuerySet with automatic organization filtering support"""

    def for_org(self, org):
        """Filter queryset by organization"""
        return self.filter(org=org)

    def for_request(self, request):
        """Filter queryset by organization from request"""
        if hasattr(request, "profile") and request.profile:
            return self.filter(org=request.profile.org)
        return self.none()


class OrgScopedManager(models.Manager):
    """Manager that uses OrgScopedQuerySet"""

    def get_queryset(self):
        return OrgScopedQuerySet(self.model, using=self._db)

    def for_org(self, org):
        return self.get_queryset().for_org(org)

    def for_request(self, request):
        return self.get_queryset().for_request(request)


class BaseOrgModel(BaseModel):
    """
    Base model for all organization-scoped entities.

    All tenant-owned models should inherit from this instead of BaseModel.
    This ensures:
    - Required org field (no null values)
    - Per-org indexes for performance
    - OrgScopedManager for easier filtering

    RLS Protection:
    ---------------
    Models inheriting from BaseOrgModel are protected by PostgreSQL Row-Level
    Security (RLS) policies. The database automatically filters rows by the
    current organization context (app.current_org session variable).

    RLS Configuration: See common/rls/__init__.py for policy definitions.
    Management: Use `python manage.py manage_rls --status` to check status.

    IMPORTANT: RLS is bypassed if the database user is a superuser.
    """

    org = models.ForeignKey(
        "common.Org",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        help_text="Organization this record belongs to",
    )

    objects = OrgScopedManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["org", "-created_at"]),
        ]

    def save(self, *args, **kwargs):
        # Validate org is set
        if not self.org_id:
            from django.core.exceptions import ValidationError

            raise ValidationError("Organization (org) is required for this model")
        super().save(*args, **kwargs)
