from rest_framework import serializers
from opportunity.models import Opportunity
from accounts.serializer import AccountSerializer
from common.serializer import UserSerializer


class OpportunitySerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    closed_by = UserSerializer()
    created_by = UserSerializer()

    class Meta:
        model = Opportunity
        # fields = ‘__all__’
        fields = (
            "id",
            "name",
            "account",
            "stage",
            "currency",
            "amount",
            "lead_source",
            "probability",
            "contacts",
            "closed_by",
            "closed_on",
            "description",
            "assigned_to",
            "created_by",
            "created_on",
            "is_active",
            "tags",
            "teams",
            "company",
            "created_on_arrow",
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
        )
