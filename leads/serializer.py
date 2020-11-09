from rest_framework import serializers
from leads.models import Lead
from accounts.models import Tags
from common.serializer import UserSerializer
from contacts.serializer import ContactSerializer


class TagsSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = (
            "name",
            "slug"
        )


class LeadSerializer(serializers.ModelSerializer):
    # user = UserSerializer()
    assigned_to = UserSerializer(read_only=True, many=True)
    created_by = UserSerializer()
    tags = TagsSerailizer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = Lead
        # fields = ‘__all__’
        fields = (
            'id',
            "title",
            "first_name",
            "last_name",
            "email",
            "phone",
            "status",
            "source",
            "address_line",
            "street",
            "city",
            "state",
            "postcode",
            "country",
            "website",
            "description",
            "assigned_to",
            "account_name",
            "opportunity_amount",
            "created_by",
            "created_on",
            "is_active",
            "enquery_type",
            "tags",
            "contacts",
            "created_from_site",
            "teams",
            "company",
            # "phone_raw_input",
            # "created_on_arrow",
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
        )
