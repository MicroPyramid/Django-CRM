from rest_framework import serializers

from accounts.serializer import AccountSerializer
from common.models import Tags
from common.serializer import (AttachmentsSerializer, OrganizationSerializer,
                               ProfileSerializer, TeamsSerializer,
                               UserSerializer)
from contacts.serializer import ContactSerializer
from opportunity.models import Opportunity


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class OpportunitySerializer(serializers.ModelSerializer):
    """Serializer for reading Opportunity data"""
    account = AccountSerializer()
    closed_by = ProfileSerializer()
    created_by = UserSerializer()
    org = OrganizationSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    opportunity_attachment = AttachmentsSerializer(read_only=True, many=True)
    get_team_users = ProfileSerializer(read_only=True, many=True)
    get_team_and_assigned_users = ProfileSerializer(read_only=True, many=True)
    get_assigned_users_not_in_teams = ProfileSerializer(read_only=True, many=True)

    class Meta:
        model = Opportunity
        fields = (
            "id",
            # Core Opportunity Information
            "name",
            "account",
            "stage",
            "opportunity_type",
            # Financial Information
            "currency",
            "amount",
            "probability",
            "closed_on",
            # Source & Context
            "lead_source",
            # Relationships
            "contacts",
            # Assignment
            "assigned_to",
            "teams",
            "closed_by",
            # Tags
            "tags",
            # Notes
            "description",
            # Related
            "opportunity_attachment",
            # System
            "created_by",
            "created_at",
            "is_active",
            "org",
            "created_on_arrow",
            "get_team_users",
            "get_team_and_assigned_users",
            "get_assigned_users_not_in_teams",
        )


class OpportunityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Opportunity data"""
    probability = serializers.IntegerField(max_value=100, required=False, allow_null=True)
    closed_on = serializers.DateField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        if request_obj:
            self.org = request_obj.profile.org

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
            # Core Opportunity Information
            "name",
            "account",
            "stage",
            "opportunity_type",
            # Financial Information
            "currency",
            "amount",
            "probability",
            "closed_on",
            # Source & Context
            "lead_source",
            # Notes
            "description",
        )

class OpportunityCreateSwaggerSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField()
    opportunity_attachment = serializers.FileField()
    class Meta:
        model = Opportunity
        fields = (
            "name",
            "account",
            "stage",
            "opportunity_type",
            "amount",
            "currency",
            "probability",
            "closed_on",
            "lead_source",
            "description",
            "assigned_to",
            "contacts",
            "teams",
            "tags",
            "opportunity_attachment"
        )

class OpportunityDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    opportunity_attachment = serializers.FileField()

class OpportunityCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
