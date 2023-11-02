from rest_framework import serializers

from accounts.models import Account, AccountEmail, Tags, AccountEmailLog
from common.serializer import (
    AttachmentsSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    UserSerializer
)
from contacts.serializer import ContactSerializer
from leads.serializer import LeadSerializer
from teams.serializer import TeamsSerializer


class TagsSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class AccountSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    lead = LeadSerializer()
    org = OrganizationSerializer()
    tags = TagsSerailizer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    account_attachment = AttachmentsSerializer(read_only=True, many=True)

    class Meta:
        model = Account
        # fields = ‘__all__’
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "industry",
            "billing_address_line",
            "billing_street",
            "billing_city",
            "billing_state",
            "billing_postcode",
            "billing_country",
            "website",
            "description",
            "account_attachment",
            "created_by",
            "created_at",
            "is_active",
            "tags",
            "status",
            "lead",
            "contact_name",
            "contacts",
            "assigned_to",
            "teams",
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


class AccountReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ["name", "billing_city", "tags"]

class AccountWriteSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Account
        fields = ["name","phone", "email", "billing_address_line","billing_street","billing_city", "billing_state", "billing_postcode","billing_country","contacts", "teams", "assigned_to","tags","account_attachment", "website", "status","lead"]


class AccountCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop("account", False)
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.fields["status"].required = False
        if account_view:
            self.fields["billing_address_line"].required = True
            self.fields["billing_street"].required = True
            self.fields["billing_city"].required = True
            self.fields["billing_state"].required = True
            self.fields["billing_postcode"].required = True
            self.fields["billing_country"].required = True

        if self.instance:
            self.fields["lead"].required = False
        self.fields["lead"].required = False
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
            "name",
            "phone",
            "email",
            "website",
            "industry",
            "description",
            "status",
            "billing_address_line",
            "billing_street",
            "billing_city",
            "billing_state",
            "billing_postcode",
            "billing_country",
            "lead",
            "contact_name",
        )

class AccountDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    account_attachment = serializers.FileField()

class AccountCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()

class EmailWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountEmail
        fields = ("from_email", "recipients", "message_subject","scheduled_later","timezone","scheduled_date_time","message_body")