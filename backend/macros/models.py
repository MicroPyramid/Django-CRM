from django.db import models

from common.base import BaseModel
from common.models import Org, Profile


class Macro(BaseModel):
    """Reusable canned response template applied to a case comment composer.

    Per `docs/cases/COORDINATION_DECISIONS.md` D2 we inherit BaseModel and
    declare our own org FK rather than using BaseOrgModel. Macros are either
    `org`-scoped (visible to everyone in the org, admin-managed) or
    `personal` (visible only to the owning Profile).
    """

    SCOPE_ORG = "org"
    SCOPE_PERSONAL = "personal"
    SCOPE_CHOICES = [
        (SCOPE_ORG, "Org"),
        (SCOPE_PERSONAL, "Personal"),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, default=SCOPE_ORG)
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="personal_macros",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)

    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="macros")

    class Meta:
        verbose_name = "Macro"
        verbose_name_plural = "Macros"
        db_table = "macro"
        ordering = ("-updated_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(scope="org", owner__isnull=True)
                    | models.Q(scope="personal", owner__isnull=False)
                ),
                name="macro_scope_owner_consistent",
            ),
        ]
        indexes = [
            models.Index(fields=["org", "scope", "is_active"]),
            models.Index(fields=["owner", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.scope})"
