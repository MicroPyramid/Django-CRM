from teams.models import Teams
from rest_framework import serializers
from common.serializer import UserSerializer, CompanySerializer


class TeamsSerializer(serializers.ModelSerializer):
    users = UserSerializer(read_only=True, many=True)
    created_by = UserSerializer()
    company = CompanySerializer()

    class Meta:
        model = Teams
        fields = (
            "id",
            "name",
            "description",
            "users",
            "created_on",
            "created_by",
            "company",
            "created_on_arrow",
        )

class TeamCreateSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(TeamCreateSerializer, self).__init__(*args, **kwargs)

        self.fields["name"].required = True

        self.company = request_obj.company

    def validate_name(self, name):
        if self.instance:
            if Teams.objects.filter(
                    name__iexact=name,
                    company=self.company,
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Team already exists with this name")
        else:
            if Teams.objects.filter(
                name__iexact=name, company=self.company
            ).exists():                
                raise serializers.ValidationError(
                    "Team already exists with this name")
        return name

    class Meta:
        model = Teams
        fields = (
            "name",
            "description",
            "created_on",
            "created_by",
            "company",
            "created_on_arrow",
        )