from rest_framework import serializers

from common.serializer import (
    BillingAddressSerializer,
    OrganizationSerializer,
    UserSerializer,
)
from invoices.models import Invoice, InvoiceHistory
from teams.serializer import TeamsSerializer


class InvoiceSerailizer(serializers.ModelSerializer):
    from_address = BillingAddressSerializer()
    to_address = BillingAddressSerializer()
    created_by = UserSerializer()
    org = OrganizationSerializer()
    teams = TeamsSerializer(read_only=True, many=True)
    assigned_to = UserSerializer(read_only=True, many=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_title",
            "invoice_number",
            "status",
            "due_date",
            "name",
            "email",
            "phone",
            "from_address",
            "to_address",
            "created_at",
            "created_by",
            "currency",
            "quantity",
            "rate",
            "tax",
            "total_amount",
            "amount_due",
            "amount_paid",
            "is_email_sent",
            "details",
            "teams",
            "assigned_to",
            "org",
        )


class InvoiceHistorySerializer(serializers.ModelSerializer):
    updated_by = UserSerializer()

    class Meta:
        model = InvoiceHistory
        fields = (
            "id",
            "invoice_title",
            "invoice_number",
            "status",
            "due_date",
            "name",
            "email",
            "phone",
            "created_at",
            "currency",
            "quantity",
            "rate",
            "total_amount",
            "amount_due",
            "amount_paid",
            "is_email_sent",
            "details",
            "updated_by",
        )


class InvoiceCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        invoice_view = kwargs.pop("invoice", False)
        request_obj = kwargs.pop("request_obj", None)
        super(InvoiceCreateSerializer, self).__init__(*args, **kwargs)

        self.org = request_obj.profile.org

    def validate_invoice_title(self, invoice_title):
        if self.instance:
            if (
                Invoice.objects.filter(
                    invoice_title__iexact=invoice_title, org=self.org
                )
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Invoice already exists with this invoice_title"
                )
        else:
            if Invoice.objects.filter(
                invoice_title__iexact=invoice_title, org=self.org
            ).exists():
                raise serializers.ValidationError(
                    "Invoice already exists with this invoice_title"
                )
        return invoice_title

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_title",
            "status",
            "name",
            "email",
            "phone",
            "due_date",
            "created_at",
            "created_by",
            "currency",
            "quantity",
            "rate",
            "tax",
            "total_amount",
            "amount_due",
            "amount_paid",
            "is_email_sent",
            "details",
            "org",
        )

class InvoiceSwaggerSerailizer(serializers.ModelSerializer):

    from_address = BillingAddressSerializer()
    to_address = BillingAddressSerializer()
    assigned_to = UserSerializer(read_only=True, many=True)
    quality_hours = serializers.CharField()
    class Meta:
        model = Invoice
        fields = (
            "invoice_title",
            "status",
            "name",
            "email",
            "phone",
            "due_date",
            "currency",
            "rate",
            "tax",
            "total_amount",
            "details",
            "teams",
            "from_address",
            "to_address",
            "assigned_to",
            "currency",
            "accounts",
            "quality_hours"
        )


