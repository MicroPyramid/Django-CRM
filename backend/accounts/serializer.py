from rest_framework import serializers

from accounts.models import Account, AccountEmail, AccountEmailLog
from common.models import Tags
from common.serializer import (
    AttachmentsSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer


class TagsSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for reading Account data"""

    created_by = UserSerializer()
    org = OrganizationSerializer()
    tags = TagsSerailizer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    account_attachment = AttachmentsSerializer(read_only=True, many=True)
    get_team_users = ProfileSerializer(read_only=True, many=True)
    get_team_and_assigned_users = ProfileSerializer(read_only=True, many=True)
    get_assigned_users_not_in_teams = ProfileSerializer(read_only=True, many=True)
    country = serializers.SerializerMethodField()

    def get_country(self, obj):
        return obj.get_country_display() if obj.country else None

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
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
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
            # System
            "created_by",
            "created_at",
            "is_active",
            "org",
            "created_on_arrow",
            "get_team_users",
            "get_team_and_assigned_users",
            "get_assigned_users_not_in_teams",
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


class AccountReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ["name", "city", "tags"]


class AccountWriteSerializer(serializers.ModelSerializer):

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
            "contacts",
            "teams",
            "assigned_to",
            "tags",
            "account_attachment",
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
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Notes
            "description",
        )


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
