from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.models import Account, AccountEmail, AccountEmailLog
from common.serializer import (
    AttachmentsSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    TagsSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer


# Note: Removed unused serializer properties that were computed but never used by frontend:
# - get_team_users, get_team_and_assigned_users, get_assigned_users_not_in_teams
# - created_on_arrow (frontend computes its own humanized timestamps)


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for reading Account data"""

    created_by = UserSerializer()
    org = OrganizationSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    account_attachment = AttachmentsSerializer(read_only=True, many=True)
    country_display = serializers.SerializerMethodField()
    cases = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    opportunities = serializers.SerializerMethodField()

    @extend_schema_field(str)
    def get_country_display(self, obj):
        return obj.get_country_display() if obj.country else None

    @extend_schema_field(list)
    def get_cases(self, obj):
        """Return cases linked to this account"""
        return [{"id": str(c.id), "name": c.name} for c in obj.accounts_cases.all()]

    @extend_schema_field(list)
    def get_tasks(self, obj):
        """Return tasks linked to this account"""
        return [{"id": str(t.id), "title": t.title} for t in obj.accounts_tasks.all()]

    @extend_schema_field(list)
    def get_opportunities(self, obj):
        """Return opportunities linked to this account"""
        return [
            {
                "id": str(o.id),
                "name": o.name,
                "stage": o.stage,
                "amount": str(o.amount) if o.amount else "0",
            }
            for o in obj.opportunities.all()
        ]

    class Meta:
        model = Account
        fields = (
            "id",
            # Core Account Information
            "name",
            "email",
            "phone",
            "website",
            # Business Information
            "industry",
            "number_of_employees",
            "annual_revenue",
            "currency",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            "country_display",
            # Assignment
            "assigned_to",
            "teams",
            "contacts",
            # Tags
            "tags",
            # Notes
            "description",
            # Related
            "account_attachment",
            "cases",
            "tasks",
            "opportunities",
            # System
            "created_by",
            "created_at",
            "is_active",
            "org",
        )


class EmailSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = AccountEmail
        fields = (
            "message_subject",
            "message_body",
            "timezone",
            "scheduled_date_time",
            "scheduled_later",
            "created_at",
            "from_email",
            "rendered_message_body",
        )

    def validate_message_body(self, message_body):
        count = 0
        for i in message_body:
            if i == "{":
                count += 1
            elif i == "}":
                count -= 1
            if count < 0:
                raise serializers.ValidationError(
                    "Brackets do not match, Enter valid tags."
                )
        if count != 0:
            raise serializers.ValidationError(
                "Brackets do not match, Enter valid tags."
            )
        return message_body


class EmailLogSerializer(serializers.ModelSerializer):
    email = EmailSerializer()

    class Meta:
        model = AccountEmailLog
        fields = ["email", "contact", "is_sent"]


class AccountWriteSerializer(serializers.ModelSerializer):
    """Serializer for API documentation of Account write operations"""

    class Meta:
        model = Account
        fields = [
            "name",
            "phone",
            "email",
            "website",
            "industry",
            "number_of_employees",
            "annual_revenue",
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            "description",
        ]


class AccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Account data"""

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        kwargs.pop("account", None)  # Remove unused 'account' parameter passed by views
        super().__init__(*args, **kwargs)
        if request_obj:
            self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if self.instance.name != name:
                if not Account.objects.filter(name__iexact=name, org=self.org).exists():
                    return name
                raise serializers.ValidationError(
                    "Account already exists with this name"
                )
            return name
        if not Account.objects.filter(name__iexact=name, org=self.org).exists():
            return name
        raise serializers.ValidationError("Account already exists with this name")

    class Meta:
        model = Account
        fields = (
            # Core Account Information
            "name",
            "email",
            "phone",
            "website",
            # Business Information
            "industry",
            "number_of_employees",
            "annual_revenue",
            "currency",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Notes
            "description",
            # Status
            "is_active",
        )

    def create(self, validated_data):
        # Default currency from org if not provided and has annual_revenue
        if not validated_data.get("currency") and validated_data.get("annual_revenue"):
            request = self.context.get("request")
            if request and hasattr(request, "profile") and request.profile.org:
                validated_data["currency"] = request.profile.org.default_currency
        return super().create(validated_data)


class AccountDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    account_attachment = serializers.FileField()


class AccountCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


class EmailWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountEmail
        fields = (
            "from_email",
            "recipients",
            "message_subject",
            "scheduled_later",
            "timezone",
            "scheduled_date_time",
            "message_body",
        )
