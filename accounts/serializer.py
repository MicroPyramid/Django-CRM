from rest_framework import serializers
from accounts.models import Account, Email, Tags
from common.serializer import UserSerializer, AttachmentsSerializer
from leads.serializer import LeadSerializer
from teams.serializer import TeamsSerializer
from contacts.serializer import ContactSerializer


class TagsSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class AccountSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    lead = LeadSerializer()
    tags = TagsSerailizer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)
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
            "created_on",
            "is_active",
            "tags",
            "status",
            "lead",
            "contact_name",
            "contacts",
            "assigned_to",
            "teams",
        )


class EmailSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(EmailSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Email
        fields = (
            "message_subject",
            "message_body",
            "timezone",
            "scheduled_date_time",
            "scheduled_later",
            "created_on",
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
        model = Email
        fields = "email" "contact" "is_sent"


class AccountCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop("account", False)
        request_obj = kwargs.pop("request_obj", None)
        super(AccountCreateSerializer, self).__init__(*args, **kwargs)
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

    def validate_name(self, name):
        if self.instance:
            if self.instance.name != name:
                if not Account.objects.filter(name__iexact=name).exists():
                    return name
                raise serializers.ValidationError(
                    "Account already exists with this name"
                )
            return name
        if not Account.objects.filter(name__iexact=name).exists():
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
        )
