from rest_framework import serializers
from cases.models import Case
from common.serializer import UserSerializer, CompanySerializer
from teams.serializer import TeamsSerializer
from accounts.serializer import AccountSerializer
from contacts.serializer import ContactSerializer


class CaseSerializer(serializers.ModelSerializer):
    account = AccountSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    teams = TeamsSerializer(read_only=True, many=True)
    company = CompanySerializer()
    get_team_users = UserSerializer(read_only=True, many=True)
    get_team_and_assigned_users = UserSerializer(read_only=True, many=True)
    get_assigned_users_not_in_teams = UserSerializer(read_only=True, many=True)


    class Meta:
        model = Case
        fields = (
            'id',
            'name',
            'status',
            'priority',
            'case_type',
            'account',
            'contacts',
            'closed_on',
            'description',
            'assigned_to',
            'created_by',
            'created_on',
            'is_active',
            'teams',
            'company',
            'get_team_users',
            'get_team_and_assigned_users',
            "get_assigned_users_not_in_teams",
            "created_on_arrow",
        )
