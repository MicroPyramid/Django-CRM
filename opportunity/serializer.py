from rest_framework import serializers
from opportunity.models import Opportunity
from accounts.serializer import AccountSerializer
from contacts.serializer import ContactSerializer
from teams.serializer import TeamsSerializer
from common.serializer import UserSerializer, CompanySerializer, AttachmentsSerializer
from accounts.models import Tags

class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = ("id", "name", "slug")

class OpportunitySerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    closed_by = UserSerializer()
    created_by = UserSerializer()
    company = CompanySerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    opportunity_attachment = AttachmentsSerializer(read_only=True, many=True)

    class Meta:
        model = Opportunity
        # fields = ‘__all__’
        fields = (
            "id",
            "name",
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
            "opportunity_attachment",
            "teams",
            "company",
            "created_on_arrow",
            "account",
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
        )

class OpportunityCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(max_value=100)
    closed_on = serializers.DateField

    def __init__(self, *args, **kwargs):
        opportunity_view = kwargs.pop("opportunity", False)
        request_obj = kwargs.pop("request_obj", None)
        super(OpportunityCreateSerializer, self).__init__(*args, **kwargs)

        self.company = request_obj.company

    def validate_name(self, name):
        if self.instance:
            if Opportunity.objects.filter(
                name__iexact=name, company=self.company
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Opportunity already exists with this name"
                )

        else:
            if Opportunity.objects.filter(
                name__iexact=name, company=self.company
            ).exists():               
                raise serializers.ValidationError(
                    "Opportunity already exists with this name"
                )
        return name

    class Meta:
        model = Opportunity
        fields = (
            "name",
            "account",
            "stage",
            "currency",
            "amount",
            "lead_source",
            "probability",
            "closed_on",
            "description",
            "created_by",
            "created_on",
            "is_active",
            "company",
            "created_on_arrow",
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
        )
