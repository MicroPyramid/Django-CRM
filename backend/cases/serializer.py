from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.serializer import AccountSerializer
from cases.models import Case
from common.serializer import (
    OrganizationSerializer,
    ProfileSerializer,
    TagsSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer


class CaseSerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    contacts = ContactSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    teams = TeamsSerializer(read_only=True, many=True)
    tags = TagsSerializer(read_only=True, many=True)
    org = OrganizationSerializer()
    created_on_arrow = serializers.SerializerMethodField()

    @extend_schema_field(str)
    def get_created_on_arrow(self, obj):
        return obj.created_on_arrow

    class Meta:
        model = Case
        fields = (
            "id",
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "description",
            "created_by",
            "created_at",
            "is_active",
            "account",
            "contacts",
            "teams",
            "assigned_to",
            "tags",
            "org",
            "created_on_arrow",
        )


class CaseCreateSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField(required=False, allow_null=True)
    org = serializers.PrimaryKeyRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if (
                Case.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Case already exists with this name")

        else:
            if Case.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError("Case already exists with this name")
        return name

    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "description",
            "is_active",
            "account",
            "org",
        )
        read_only_fields = ("org",)


class CaseCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "teams",
            "assigned_to",
            "account",
            "contacts",
            "tags",
            "description",
        )


class CaseDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    case_attachment = serializers.FileField()


class CaseCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
