from rest_framework import serializers
from opportunity.models import Opportunity
from accounts.serializer import AccountSerializer
from contacts.serializer import ContactSerializer
from teams.serializer import TeamsSerializer
from common.serializer import ProfileSerializer, AttachmentsSerializer
from accounts.models import Tags


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class OpportunitySerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    closed_by = ProfileSerializer()
    created_by = ProfileSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
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
        self.org = request_obj.org

    def validate_name(self, name):
        if self.instance:
            if (
                Opportunity.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Opportunity already exists with this name"
                )

        else:
            if Opportunity.objects.filter(name__iexact=name, org=self.org).exists():
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
            "created_on_arrow",
            "org"
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
        )
