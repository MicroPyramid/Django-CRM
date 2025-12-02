from rest_framework import serializers

from accounts.models import Account
from common.models import Tags
from common.serializer import (
    AttachmentsSerializer,
    LeadCommentSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer
from leads.models import Lead


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class LeadSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    created_by = UserSerializer()
    country = serializers.SerializerMethodField()
    tags = TagsSerializer(read_only=True, many=True)
    lead_attachment = AttachmentsSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    lead_comments = LeadCommentSerializer(read_only=True, many=True)
    converted_account = serializers.PrimaryKeyRelatedField(read_only=True)
    converted_contact = serializers.PrimaryKeyRelatedField(read_only=True)
    converted_opportunity = serializers.PrimaryKeyRelatedField(read_only=True)
    conversion_date = serializers.DateTimeField(read_only=True)

    def get_country(self, obj):
        return obj.get_country_display()

    class Meta:
        model = Lead
        fields = (
            "id",
            # Core Lead Information
            "salutation",
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "website",
            "linkedin_url",
            # Sales Pipeline
            "status",
            "source",
            "industry",
            "rating",
            "opportunity_amount",
            "probability",
            "close_date",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Assignment
            "assigned_to",
            "teams",
            # Activity
            "last_contacted",
            "next_follow_up",
            "description",
            # Related
            "contacts",
            "lead_attachment",
            "lead_comments",
            "tags",
            # System
            "created_by",
            "created_at",
            "is_active",
            "created_from_site",
            "company_name",
            "converted_account",
            "converted_contact",
            "converted_opportunity",
            "conversion_date",
        )


class LeadCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(
        max_value=100, required=False, allow_null=True
    )
    opportunity_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    close_date = serializers.DateField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        if self.initial_data and self.initial_data.get("status") == "converted":
            self.fields["email"].required = True
        self.fields["first_name"].required = False
        self.fields["last_name"].required = False
        self.fields["salutation"].required = False
        self.org = request_obj.profile.org

        if self.instance:
            if self.instance.created_from_site:
                prev_choices = self.fields["source"]._get_choices()
                prev_choices = prev_choices + [("micropyramid", "Micropyramid")]
                self.fields["source"]._set_choices(prev_choices)

    class Meta:
        model = Lead
        fields = (
            # Core Lead Information
            "salutation",
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "website",
            "linkedin_url",
            # Sales Pipeline
            "status",
            "source",
            "industry",
            "rating",
            "opportunity_amount",
            "probability",
            "close_date",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Activity
            "last_contacted",
            "next_follow_up",
            "description",
            # System
            "company_name",
            "is_active",
        )


class LeadCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            # Core Lead Information
            "salutation",
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "website",
            "linkedin_url",
            # Sales Pipeline
            "status",
            "source",
            "industry",
            "rating",
            "opportunity_amount",
            "probability",
            "close_date",
            # Address
            "address_line",
            "city",
            "state",
            "postcode",
            "country",
            # Assignment & Related
            "assigned_to",
            "teams",
            "contacts",
            "tags",
            # Activity
            "last_contacted",
            "next_follow_up",
            "description",
            # System
            "company_name",
            "lead_attachment",
        ]


class CreateLeadFromSiteSwaggerSerializer(serializers.Serializer):
    apikey = serializers.CharField()
    title = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.CharField()
    source = serializers.CharField()
    description = serializers.CharField()


class LeadDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    lead_attachment = serializers.FileField()


class LeadCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


class LeadUploadSwaggerSerializer(serializers.Serializer):
    leads_file = serializers.FileField()
