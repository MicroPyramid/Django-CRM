from rest_framework import serializers
from accounts.models import Account, Email, Tags
from common.serializer import UserSerializer, CompanySerializer
from leads.serializer import LeadSerializer
from teams.serializer import TeamsSerializer
from contacts.serializer import ContactSerializer


class TagsSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = (
            "name",
            "slug"
        )


class AccountSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    lead = LeadSerializer()
    company = CompanySerializer()
    tags = TagsSerailizer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)

    class Meta:
        model = Account
        # fields = ‘__all__’
        fields = (
            'id',
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
            "company"
        )


class EmailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Email
        fields = (
            "from_account"
            "recipients"
            "message_subject"
            "message_body"
            "timezone"
            "scheduled_date_time"
            "scheduled_later"
            "created_on"
            "from_email"
            "rendered_message_body"
        )


class EmailLogSerializer(serializers.ModelSerializer):
    email = EmailSerializer()

    class Meta:
        model = Email
        fields = (
            "email"
            "contact"
            "is_sent"
        )
