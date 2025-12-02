"""
Solution (Knowledge Base) Serializers
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from cases.models import Case, Solution
from common.serializer import OrganizationSerializer


class SolutionSerializer(serializers.ModelSerializer):
    """Serializer for Solution model"""

    org = OrganizationSerializer(read_only=True)
    case_count = serializers.SerializerMethodField()

    class Meta:
        model = Solution
        fields = [
            "id",
            "title",
            "description",
            "status",
            "is_published",
            "org",
            "case_count",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "org",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    @extend_schema_field(int)
    def get_case_count(self, obj):
        """Get number of cases using this solution"""
        return obj.cases.count()


class SolutionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating solutions"""

    class Meta:
        model = Solution
        fields = [
            "title",
            "description",
            "status",
            "is_published",
        ]

    def validate_is_published(self, value):
        """Only approved solutions can be published"""
        if value and self.instance:
            if self.instance.status != "approved":
                raise serializers.ValidationError(
                    "Only approved solutions can be published. Please set status to 'approved' first."
                )
        return value


class SolutionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for solution with linked cases"""

    org = OrganizationSerializer(read_only=True)
    linked_cases = serializers.SerializerMethodField()

    class Meta:
        model = Solution
        fields = [
            "id",
            "title",
            "description",
            "status",
            "is_published",
            "org",
            "linked_cases",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    @extend_schema_field(list)
    def get_linked_cases(self, obj):
        """Get cases that use this solution"""
        from cases.serializer import CaseSerializer

        return CaseSerializer(obj.cases.all()[:10], many=True).data
