"""DRF serializers for the macros REST API."""

from rest_framework import serializers

from macros.models import Macro


class MacroSerializer(serializers.ModelSerializer):
    """Serialize Macro for read and (admin) write paths.

    Scope/owner enforcement happens in the view because it depends on the
    requesting profile (admin can create org macros, others cannot).
    """

    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Macro
        fields = (
            "id",
            "title",
            "body",
            "scope",
            "owner",
            "owner_name",
            "is_active",
            "usage_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "owner_name",
            "usage_count",
            "created_at",
            "updated_at",
        )

    def get_owner_name(self, obj):
        # `User` only stores `email` — no first_name/last_name on this model
        # — so we surface the email directly. Frontend can display whatever
        # form it wants from there.
        if obj.owner is None or obj.owner.user is None:
            return None
        return obj.owner.user.email or None
