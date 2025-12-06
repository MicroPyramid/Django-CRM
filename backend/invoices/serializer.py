from rest_framework import serializers

from common.serializer import (
    BillingAddressSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    TeamsSerializer,
    UserSerializer,
)
from invoices.models import Invoice, InvoiceHistory


class InvoiceSerailizer(serializers.ModelSerializer):
    from_address = BillingAddressSerializer()
    to_address = BillingAddressSerializer()
    created_by = ProfileSerializer()
    org = OrganizationSerializer()
    teams = TeamsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)

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
    updated_by = ProfileSerializer()

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

    def create(self, validated_data):
        # Default currency from org if not provided
        if not validated_data.get("currency"):
            request = self.context.get("request")
            if request and hasattr(request, "profile") and request.profile.org:
                validated_data["currency"] = request.profile.org.default_currency
        return super().create(validated_data)


class InvoiceSwaggerSerailizer(serializers.ModelSerializer):

    from_address = BillingAddressSerializer()
    to_address = BillingAddressSerializer()
    assigned_to = ProfileSerializer(read_only=True, many=True)
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
            "quality_hours",
        )


# Phase 3: Product and Line Item Serializers

from invoices.models import InvoiceLineItem, Product


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product"""

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "org",
        )

    def create(self, validated_data):
        # Default currency from org if not provided and has price
        if not validated_data.get("currency") and validated_data.get("price"):
            request = self.context.get("request")
            if request and hasattr(request, "profile") and request.profile.org:
                validated_data["currency"] = request.profile.org.default_currency
        return super().create(validated_data)


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Invoice Line Items"""

    product_name = serializers.CharField(source="product.name", read_only=True)
    formatted_unit_price = serializers.CharField(read_only=True)
    formatted_total = serializers.CharField(read_only=True)

    class Meta:
        model = InvoiceLineItem
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "total",
        )


class InvoiceWithLineItemsSerializer(serializers.ModelSerializer):
    """Enhanced Invoice Serializer with Line Items"""

    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    created_by = ProfileSerializer(read_only=True)
    org = OrganizationSerializer(read_only=True)
    teams = TeamsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    line_items_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    line_items_count = serializers.IntegerField(read_only=True)

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
            "created_at",
            "created_by",
            "currency",
            "tax",
            "total_amount",
            "amount_due",
            "amount_paid",
            "is_email_sent",
            "details",
            "teams",
            "assigned_to",
            "org",
            "line_items",
            "line_items_total",
            "line_items_count",
        )
