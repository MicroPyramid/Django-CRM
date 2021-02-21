from rest_framework import serializers
from cases.models import Case
from common.serializer import UserSerializer, CompanySerializer
from teams.serializer import TeamsSerializer
from accounts.serializer import AccountSerializer
from contacts.serializer import ContactSerializer


class CaseSerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    contacts = ContactSerializer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    teams = TeamsSerializer(read_only=True, many=True)
    company = CompanySerializer()

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
            "created_on",
            "is_active",
            "account",
            "contacts",
            "teams",
            "assigned_to",
            "company",
            "created_on_arrow",
        )


class CaseCreateSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField

    def __init__(self, *args, **kwargs):
        case_view = kwargs.pop("case", False)
        request_obj = kwargs.pop("request_obj", None)
        super(CaseCreateSerializer, self).__init__(*args, **kwargs)

        self.company = request_obj.company

    def validate_name(self, name):
        if self.instance:
            if (
                Case.objects.filter(name__iexact=name, company=self.company)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Case already exists with this name")

        else:
            if Case.objects.filter(name__iexact=name, company=self.company).exists():
                raise serializers.ValidationError("Case already exists with this name")
        return name

    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "description",
            "created_by",
            "created_on",
            "is_active",
            "account",
            "company",
            "created_on_arrow",
        )
