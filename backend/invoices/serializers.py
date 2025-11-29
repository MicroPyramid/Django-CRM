from rest_framework import serializers

from accounts.serializer import AccountSerializer
from common.serializer import ProfileSerializer, TeamsSerializer, UserSerializer
from invoices.models import Invoice, InvoiceHistory


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""

    assigned_to = ProfileSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    accounts = AccountSerializer(many=True, read_only=True)
    teams = TeamsSerializer(many=True, read_only=True)

    # Write fields
    assigned_to_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    account_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    team_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "invoice_number",
        )


class InvoiceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for invoice lists"""

    assigned_to_count = serializers.SerializerMethodField()
    accounts_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_title",
            "invoice_number",
            "name",
            "email",
            "total_amount",
            "amount_due",
            "amount_paid",
            "status",
            "due_date",
            "created_at",
            "updated_at",
            "assigned_to_count",
            "accounts_count",
        ]

    def get_assigned_to_count(self, obj):
        return obj.assigned_to.count()

    def get_accounts_count(self, obj):
        return obj.accounts.count()


class InvoiceHistorySerializer(serializers.ModelSerializer):
    """Serializer for Invoice History"""

    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = InvoiceHistory
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
