from rest_framework import serializers
from contacts.models import Contact
from common.serializer import (
    UserSerializer,
    BillingAddressSerializer,
    AttachmentsSerializer,
)
from teams.serializer import TeamsSerializer


class ContactSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    teams = TeamsSerializer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)
    address = BillingAddressSerializer(read_only=True)
    get_team_users = UserSerializer(read_only=True, many=True)
    get_team_and_assigned_users = UserSerializer(read_only=True, many=True)
    get_assigned_users_not_in_teams = UserSerializer(read_only=True, many=True)
    contact_attachment = AttachmentsSerializer(read_only=True, many=True)

    class Meta:
        model = Contact
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "description",
            "contact_attachment",
            "assigned_to",
            "created_by",
            "created_on",
            "is_active",
            "teams",
            "created_on_arrow",
            "get_team_users",
            "get_team_and_assigned_users",
            "get_assigned_users_not_in_teams",
        )


class CreateContactSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        contact_view = kwargs.pop("contact", False)
        request_obj = kwargs.pop("request_obj", None)
        super(CreateContactSerializer, self).__init__(*args, **kwargs)

    def validate_first_name(self, first_name):
        if self.instance:
            if (
                Contact.objects.filter(first_name__iexact=first_name)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Contact already exists with this name"
                )

        else:
            if Contact.objects.filter(first_name__iexact=first_name).exists():
                raise serializers.ValidationError(
                    "Contact already exists with this name"
                )
        return first_name

    class Meta:
        model = Contact
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "description",
        )
