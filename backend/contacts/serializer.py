from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.serializer import (
    AttachmentsSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    TeamsSerializer,
)
from contacts.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for reading Contact data"""

    teams = TeamsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    get_team_users = ProfileSerializer(read_only=True, many=True)
    get_team_and_assigned_users = ProfileSerializer(read_only=True, many=True)
    get_assigned_users_not_in_teams = ProfileSerializer(read_only=True, many=True)
    contact_attachment = AttachmentsSerializer(read_only=True, many=True)
    org = OrganizationSerializer()
    country = serializers.SerializerMethodField()
    created_on_arrow = serializers.SerializerMethodField()

    @extend_schema_field(str)
    def get_country(self, obj):
        return obj.get_country_display()

    @extend_schema_field(str)
    def get_created_on_arrow(self, obj):
        return obj.created_on_arrow

    class Meta:
        model = Contact
        fields = (
            "id",
            # Core Contact Information
            "first_name",
            "last_name",
            "email",
            "phone",
            # Professional Information
            "organization",
            "title",
            "department",
            # Communication Preferences
            "do_not_call",
            "linkedin_url",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Assignment
            "assigned_to",
            "teams",
            # Tags
            "tags",
            # Notes
            "description",
            # System
            "created_by",
            "created_at",
            "is_active",
            "org",
            "account",
            "created_on_arrow",
            "get_team_users",
            "get_team_and_assigned_users",
            "get_assigned_users_not_in_teams",
            "contact_attachment",
        )


class CreateContactSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Contact data"""

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        if request_obj:
            self.org = request_obj.profile.org

    def validate_email(self, email):
        if email:
            if self.instance:
                if (
                    Contact.objects.filter(email__iexact=email, org=self.org)
                    .exclude(id=self.instance.id)
                    .exists()
                ):
                    raise serializers.ValidationError(
                        "Contact already exists with this email"
                    )
            else:
                if Contact.objects.filter(email__iexact=email, org=self.org).exists():
                    raise serializers.ValidationError(
                        "Contact already exists with this email"
                    )
        return email

    class Meta:
        model = Contact
        fields = (
            # Core Contact Information
            "first_name",
            "last_name",
            "email",
            "phone",
            # Professional Information
            "organization",
            "title",
            "department",
            # Communication Preferences
            "do_not_call",
            "linkedin_url",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Notes
            "description",
            # Account
            "account",
            # Status
            "is_active",
        )


class ContactDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    contact_attachment = serializers.FileField()


class ContactCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
