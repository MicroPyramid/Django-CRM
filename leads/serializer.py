from rest_framework import serializers
from leads.models import Lead
from accounts.models import Tags, Account
from common.serializer import UserSerializer
from contacts.serializer import ContactSerializer


class TagsSerailizer(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = ("name", "slug")


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
            "id",
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


class LeadCreateSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(LeadCreateSerializer, self).__init__(*args, **kwargs)
        if self.initial_data.get("status") == "converted":
            self.fields["account_name"].required = True
            self.fields["email"].required = True
        self.fields["first_name"].required = False
        self.fields["last_name"].required = False
        self.fields["title"].required = True

        if self.instance:
            if self.instance.created_from_site:
                prev_choices = self.fields["source"]._get_choices()
                prev_choices = prev_choices + \
                    [("micropyramid", "Micropyramid")]
                self.fields["source"]._set_choices(prev_choices)
        self.company = request_obj.company

    def clean_account_name(self, account_name):
        if self.instance:
            if self.instance.account_name != account_name:
                if not Account.objects.filter(
                    name__iexact=account_name,
                    company=self.company,
                ).exists():
                    return account_name
                raise serializers.ValidationError(
                    "Account already exists with this name")
            return account_name
        if not Account.objects.filter(
            name__iexact=account_name, company=self.company
        ).exists():
            return account_name
        raise serializers.ValidationError(
            "Account already exists with this name")

    class Meta:
        model = Lead
        fields = (
            "first_name",
            "last_name",
            "account_name",
            "title",
            "phone",
            "email",
            "status",
            "source",
            "website",
            "description",
            "address_line",
            "street",
            "city",
            "state",
            "postcode",
            "country",
        )
