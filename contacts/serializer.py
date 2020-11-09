from rest_framework import serializers
from contacts.models import Contact
from common.serializer import UserSerializer, CompanySerializer, BillingAddressSerializer
from teams.serializer import TeamsSerializer


class ContactSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    company = CompanySerializer()
    teams = TeamsSerializer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)
    address = BillingAddressSerializer(read_only=True)
    get_team_users = UserSerializer(read_only=True, many=True)
    get_team_and_assigned_users = UserSerializer(read_only=True, many=True)
    get_assigned_users_not_in_teams = UserSerializer(read_only=True, many=True)

    class Meta:
        model = Contact
        fields = (
            'id',
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "description",
            "assigned_to",
            "created_by",
            "created_on",
            "is_active",
            "teams",
            "company",
            "created_on_arrow",
            "get_team_users",
            "get_team_and_assigned_users",
            "get_assigned_users_not_in_teams",
        )


class CreateContctForm(serializers.ModelSerializer):

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
