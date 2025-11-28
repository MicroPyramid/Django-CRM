import uuid

# Third party imports
from crum import get_current_user

# Django imports
from django.db import models

# Module imports
from common.mixins import AuditModel


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
        user = get_current_user()
        if user is None or user.is_anonymous:
            self.created_by = None
            self.updated_by = None
            super(BaseModel, self).save(*args, **kwargs)
        else:
            # Check if the model is being created or updated
            if self._state.adding:
                # If created only set created_by value: set updated_by to None
                self.created_by = user
                self.updated_by = None
            # If updated only set updated_by value don't touch created_by
            self.updated_by = user
            super(BaseModel, self).save(*args, **kwargs)

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
