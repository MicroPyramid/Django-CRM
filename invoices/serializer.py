from rest_framework import serializers
from invoices.models import Invoice, InvoiceHistory
from common.serializer import (
    UserSerializer,
    CompanySerializer,
    BillingAddressSerializer,
)
from teams.serializer import TeamsSerializer


class InvoiceSerailizer(serializers.ModelSerializer):
    from_address = BillingAddressSerializer()
    to_address = BillingAddressSerializer()
    created_by = UserSerializer()
    company = CompanySerializer()
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
            "created_on",
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
            "company",
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
            "created_on",
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

        self.company = request_obj.company

    def validate_invoice_title(self, invoice_title):
        if self.instance:
            if (
                Invoice.objects.filter(
                    invoice_title__iexact=invoice_title, company=self.company
                )
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Invoice already exists with this invoice_title"
                )
        else:
            if Invoice.objects.filter(
                invoice_title__iexact=invoice_title, company=self.company
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
            "created_on",
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
            "company",
        )
