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
