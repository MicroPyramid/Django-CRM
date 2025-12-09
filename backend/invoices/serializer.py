from rest_framework import serializers

from accounts.models import Account
from accounts.serializer import AccountSerializer
from common.serializer import (
    OrganizationSerializer,
    ProfileSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from invoices.models import (
    Estimate,
    EstimateLineItem,
    Invoice,
    InvoiceHistory,
    InvoiceLineItem,
    InvoiceTemplate,
    Payment,
    Product,
    RecurringInvoice,
    RecurringInvoiceLineItem,
)
from opportunity.models import Opportunity


# =============================================================================
# MINIMAL OPPORTUNITY SERIALIZER (to avoid circular import)
# =============================================================================


class OpportunityMinimalSerializer(serializers.ModelSerializer):
    """Minimal Opportunity serializer for invoice context - avoids circular import"""

    class Meta:
        model = Opportunity
        fields = (
            "id",
            "name",
            "amount",
            "stage",
            "currency",
        )


# =============================================================================
# PRODUCT SERIALIZERS
# =============================================================================


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product catalog"""

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "description",
            "sku",
            "price",
            "currency",
            "category",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Products"""

    class Meta:
        model = Product
        fields = (
            "name",
            "description",
            "sku",
            "price",
            "currency",
            "category",
            "is_active",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "profile"):
            validated_data["org"] = request.profile.org
            # Default currency from org if not provided
            if not validated_data.get("currency") and request.profile.org:
                validated_data["currency"] = getattr(
                    request.profile.org, "default_currency", "USD"
                )
        return super().create(validated_data)


# =============================================================================
# INVOICE TEMPLATE SERIALIZERS
# =============================================================================


class InvoiceTemplateSerializer(serializers.ModelSerializer):
    """Serializer for Invoice Templates"""

    class Meta:
        model = InvoiceTemplate
        fields = (
            "id",
            "name",
            "logo",
            "primary_color",
            "secondary_color",
            "template_html",
            "template_css",
            "default_notes",
            "default_terms",
            "footer_text",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class InvoiceTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Invoice Templates"""

    class Meta:
        model = InvoiceTemplate
        fields = (
            "name",
            "logo",
            "primary_color",
            "secondary_color",
            "template_html",
            "template_css",
            "default_notes",
            "default_terms",
            "footer_text",
            "is_default",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "profile"):
            validated_data["org"] = request.profile.org
        return super().create(validated_data)


# =============================================================================
# LINE ITEM SERIALIZERS
# =============================================================================


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Invoice Line Items"""

    product_name = serializers.CharField(source="product.name", read_only=True)
    formatted_unit_price = serializers.CharField(read_only=True)
    formatted_total = serializers.CharField(read_only=True)

    class Meta:
        model = InvoiceLineItem
        fields = (
            "id",
            "product",
            "product_name",
            "name",
            "description",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "discount_amount",
            "tax_rate",
            "tax_amount",
            "subtotal",
            "total",
            "order",
            "formatted_unit_price",
            "formatted_total",
        )
        read_only_fields = (
            "id",
            "discount_amount",
            "tax_amount",
            "subtotal",
            "total",
        )


class InvoiceLineItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Invoice Line Items"""

    class Meta:
        model = InvoiceLineItem
        fields = (
            "product",
            "name",
            "description",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "tax_rate",
            "order",
        )


# =============================================================================
# PAYMENT SERIALIZERS
# =============================================================================


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payments"""

    class Meta:
        model = Payment
        fields = (
            "id",
            "invoice",
            "amount",
            "payment_date",
            "payment_method",
            "reference_number",
            "notes",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for recording Payments"""

    class Meta:
        model = Payment
        fields = (
            "amount",
            "payment_date",
            "payment_method",
            "reference_number",
            "notes",
        )


# =============================================================================
# INVOICE SERIALIZERS
# =============================================================================


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Invoice list views"""

    account_name = serializers.CharField(source="account.name", read_only=True)
    contact_name = serializers.SerializerMethodField()
    line_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "invoice_title",
            "status",
            "account",
            "account_name",
            "contact",
            "contact_name",
            "client_name",
            "client_email",
            "issue_date",
            "due_date",
            "total_amount",
            "amount_due",
            "amount_paid",
            "currency",
            "is_overdue",
            "line_items_count",
            "created_at",
        )

    def get_contact_name(self, obj):
        if obj.contact:
            return f"{obj.contact.first_name} {obj.contact.last_name}"
        return None

    def get_line_items_count(self, obj):
        return obj.line_items.count()


class InvoiceSerializer(serializers.ModelSerializer):
    """Full Invoice serializer with nested relationships"""

    account = AccountSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    opportunity = OpportunityMinimalSerializer(read_only=True)
    template = InvoiceTemplateSerializer(read_only=True)
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    org = OrganizationSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    public_url = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "invoice_title",
            "status",
            # CRM Integration
            "account",
            "contact",
            "opportunity",
            # Client Details
            "client_name",
            "client_email",
            "client_phone",
            # Billing Address
            "billing_address_line",
            "billing_city",
            "billing_state",
            "billing_postcode",
            "billing_country",
            # Client Address
            "client_address_line",
            "client_city",
            "client_state",
            "client_postcode",
            "client_country",
            # Financial
            "subtotal",
            "discount_type",
            "discount_value",
            "discount_amount",
            "tax_rate",
            "tax_amount",
            "shipping_amount",
            "total_amount",
            "currency",
            "amount_paid",
            "amount_due",
            # Dates
            "issue_date",
            "due_date",
            "payment_terms",
            "sent_at",
            "viewed_at",
            "paid_at",
            # Reminders
            "reminder_enabled",
            "reminder_days_before",
            "reminder_days_after",
            "reminder_frequency",
            "last_reminder_sent",
            "reminder_count",
            # Client Portal
            "public_token",
            "public_link_enabled",
            "public_url",
            # Template
            "template",
            # Notes
            "notes",
            "terms",
            "details",
            # Additional Metadata
            "billing_period",
            "po_number",
            # Related
            "line_items",
            "payments",
            # Assignment
            "assigned_to",
            "teams",
            # Meta
            "is_overdue",
            "created_at",
            "updated_at",
            "created_by",
            "org",
        )


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Invoices with CRM validation"""

    # CRM Integration fields - accept IDs for writing
    account_id = serializers.UUIDField(write_only=True, required=True)
    contact_id = serializers.UUIDField(write_only=True, required=True)
    opportunity_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )
    template_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )

    # Line items for bulk creation
    line_items = InvoiceLineItemCreateSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = (
            "invoice_title",
            "status",
            # CRM Integration (IDs)
            "account_id",
            "contact_id",
            "opportunity_id",
            # Client Details
            "client_name",
            "client_email",
            "client_phone",
            # Billing Address
            "billing_address_line",
            "billing_city",
            "billing_state",
            "billing_postcode",
            "billing_country",
            # Client Address
            "client_address_line",
            "client_city",
            "client_state",
            "client_postcode",
            "client_country",
            # Financial
            "discount_type",
            "discount_value",
            "tax_rate",
            "shipping_amount",
            "currency",
            # Dates
            "issue_date",
            "due_date",
            "payment_terms",
            # Reminders
            "reminder_enabled",
            "reminder_days_before",
            "reminder_days_after",
            "reminder_frequency",
            # Client Portal
            "public_link_enabled",
            # Template
            "template_id",
            # Notes
            "notes",
            "terms",
            # Additional Metadata
            "billing_period",
            "po_number",
            # Line Items
            "line_items",
        )

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = None
        if request_obj and hasattr(request_obj, "profile"):
            self.org = request_obj.profile.org

    def validate_account_id(self, value):
        """Validate account exists and belongs to org"""
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Account.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Account not found or does not belong to your organization"
            )
        return value

    def validate_contact_id(self, value):
        """Validate contact exists and belongs to org"""
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Contact.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Contact not found or does not belong to your organization"
            )
        return value

    def validate_opportunity_id(self, value):
        """Validate opportunity exists and belongs to org (if provided)"""
        if value is None:
            return value
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Opportunity.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Opportunity not found or does not belong to your organization"
            )
        return value

    def validate(self, data):
        """Cross-field validation"""
        account_id = data.get("account_id")
        contact_id = data.get("contact_id")

        # Validate contact belongs to account (if both provided)
        if account_id and contact_id and self.org:
            contact = Contact.objects.filter(id=contact_id, org=self.org).first()
            if contact and contact.account_id and contact.account_id != account_id:
                raise serializers.ValidationError(
                    {"contact_id": f"Contact does not belong to the selected account"}
                )
        return data

    def create(self, validated_data):
        line_items_data = validated_data.pop("line_items", [])

        # Set org
        validated_data["org"] = self.org

        # Create invoice
        invoice = Invoice.objects.create(**validated_data)

        # Create line items
        for idx, item_data in enumerate(line_items_data):
            InvoiceLineItem.objects.create(
                invoice=invoice,
                org=self.org,
                order=item_data.get("order", idx),
                **{k: v for k, v in item_data.items() if k != "order"},
            )

        # Recalculate totals
        invoice.recalculate_totals()
        invoice.save()

        return invoice

    def update(self, instance, validated_data):
        line_items_data = validated_data.pop("line_items", None)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle line items if provided
        if line_items_data is not None:
            # Delete existing and recreate
            instance.line_items.all().delete()
            for idx, item_data in enumerate(line_items_data):
                InvoiceLineItem.objects.create(
                    invoice=instance,
                    org=self.org or instance.org,
                    order=item_data.get("order", idx),
                    **{k: v for k, v in item_data.items() if k != "order"},
                )

        instance.recalculate_totals()
        instance.save()

        return instance


# =============================================================================
# INVOICE HISTORY SERIALIZER
# =============================================================================


class InvoiceHistorySerializer(serializers.ModelSerializer):
    """Serializer for Invoice History (audit trail)"""

    updated_by = ProfileSerializer(read_only=True)

    class Meta:
        model = InvoiceHistory
        fields = (
            "id",
            "invoice",
            "invoice_title",
            "invoice_number",
            "status",
            "client_name",
            "client_email",
            "total_amount",
            "amount_due",
            "currency",
            "due_date",
            "details",
            "updated_by",
            "created_at",
        )


# =============================================================================
# ESTIMATE SERIALIZERS
# =============================================================================


class EstimateLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Estimate Line Items"""

    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = EstimateLineItem
        fields = (
            "id",
            "product",
            "product_name",
            "name",
            "description",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "discount_amount",
            "tax_rate",
            "tax_amount",
            "subtotal",
            "total",
            "order",
        )
        read_only_fields = ("id", "discount_amount", "tax_amount", "subtotal", "total")


class EstimateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Estimate list views"""

    account_name = serializers.CharField(source="account.name", read_only=True)
    contact_name = serializers.SerializerMethodField()

    class Meta:
        model = Estimate
        fields = (
            "id",
            "estimate_number",
            "title",
            "status",
            "account",
            "account_name",
            "contact",
            "contact_name",
            "client_name",
            "issue_date",
            "expiry_date",
            "total_amount",
            "currency",
            "is_expired",
            "created_at",
        )

    def get_contact_name(self, obj):
        if obj.contact:
            return f"{obj.contact.first_name} {obj.contact.last_name}"
        return None


class EstimateSerializer(serializers.ModelSerializer):
    """Full Estimate serializer"""

    account = AccountSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    opportunity = OpportunityMinimalSerializer(read_only=True)
    converted_to_invoice = InvoiceListSerializer(read_only=True)
    line_items = EstimateLineItemSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    is_expired = serializers.BooleanField(read_only=True)
    public_url = serializers.CharField(read_only=True)

    class Meta:
        model = Estimate
        fields = "__all__"


class EstimateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Estimates"""

    account_id = serializers.UUIDField(write_only=True, required=True)
    contact_id = serializers.UUIDField(write_only=True, required=True)
    opportunity_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Estimate
        fields = (
            "title",
            "status",
            "account_id",
            "contact_id",
            "opportunity_id",
            "client_name",
            "client_email",
            "client_phone",
            "client_address_line",
            "client_city",
            "client_state",
            "client_postcode",
            "client_country",
            "discount_type",
            "discount_value",
            "tax_rate",
            "currency",
            "issue_date",
            "expiry_date",
            "public_link_enabled",
            "notes",
            "terms",
        )

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = None
        if request_obj and hasattr(request_obj, "profile"):
            self.org = request_obj.profile.org

    def validate_account_id(self, value):
        """Validate account exists and belongs to org"""
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Account.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Account not found or does not belong to your organization"
            )
        return value

    def validate_contact_id(self, value):
        """Validate contact exists and belongs to org"""
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Contact.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Contact not found or does not belong to your organization"
            )
        return value

    def validate_opportunity_id(self, value):
        """Validate opportunity exists and belongs to org (if provided)"""
        if value is None:
            return value
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Opportunity.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Opportunity not found or does not belong to your organization"
            )
        return value

    def create(self, validated_data):
        validated_data["org"] = self.org
        return super().create(validated_data)


# =============================================================================
# RECURRING INVOICE SERIALIZERS
# =============================================================================


class RecurringInvoiceLineItemSerializer(serializers.ModelSerializer):
    """Serializer for Recurring Invoice Line Items"""

    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = RecurringInvoiceLineItem
        fields = (
            "id",
            "product",
            "product_name",
            "name",
            "description",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "tax_rate",
            "order",
        )
        read_only_fields = ("id",)


class RecurringInvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Recurring Invoice list views"""

    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = RecurringInvoice
        fields = (
            "id",
            "title",
            "account",
            "account_name",
            "client_name",
            "frequency",
            "start_date",
            "end_date",
            "next_generation_date",
            "is_active",
            "auto_send",
            "total_amount",
            "currency",
            "invoices_generated",
            "created_at",
        )


class RecurringInvoiceSerializer(serializers.ModelSerializer):
    """Full Recurring Invoice serializer"""

    account = AccountSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    opportunity = OpportunityMinimalSerializer(read_only=True)
    line_items = RecurringInvoiceLineItemSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)

    class Meta:
        model = RecurringInvoice
        fields = "__all__"


class RecurringInvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Recurring Invoices"""

    account_id = serializers.UUIDField(write_only=True, required=True)
    contact_id = serializers.UUIDField(write_only=True, required=True)
    opportunity_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = RecurringInvoice
        fields = (
            "title",
            "is_active",
            "account_id",
            "contact_id",
            "opportunity_id",
            "client_name",
            "client_email",
            "frequency",
            "custom_days",
            "start_date",
            "end_date",
            "next_generation_date",
            "payment_terms",
            "auto_send",
            "currency",
            "discount_type",
            "discount_value",
            "tax_rate",
            "notes",
            "terms",
        )

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = None
        if request_obj and hasattr(request_obj, "profile"):
            self.org = request_obj.profile.org

    def validate_account_id(self, value):
        """Validate account exists and belongs to org"""
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Account.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Account not found or does not belong to your organization"
            )
        return value

    def validate_contact_id(self, value):
        """Validate contact exists and belongs to org"""
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Contact.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Contact not found or does not belong to your organization"
            )
        return value

    def validate_opportunity_id(self, value):
        """Validate opportunity exists and belongs to org (if provided)"""
        if value is None:
            return value
        if not self.org:
            raise serializers.ValidationError("Organization context required")
        if not Opportunity.objects.filter(id=value, org=self.org).exists():
            raise serializers.ValidationError(
                "Opportunity not found or does not belong to your organization"
            )
        return value

    def create(self, validated_data):
        validated_data["org"] = self.org
        return super().create(validated_data)


# =============================================================================
# PUBLIC PORTAL SERIALIZERS (No auth required)
# =============================================================================


class PublicInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for public invoice viewing (no sensitive data)"""

    line_items = InvoiceLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "invoice_number",
            "invoice_title",
            "status",
            "client_name",
            "client_email",
            "billing_address_line",
            "billing_city",
            "billing_state",
            "billing_postcode",
            "billing_country",
            "client_address_line",
            "client_city",
            "client_state",
            "client_postcode",
            "client_country",
            "subtotal",
            "discount_type",
            "discount_value",
            "discount_amount",
            "tax_rate",
            "tax_amount",
            "shipping_amount",
            "total_amount",
            "currency",
            "amount_paid",
            "amount_due",
            "issue_date",
            "due_date",
            "payment_terms",
            "notes",
            "terms",
            "line_items",
        )


class PublicEstimateSerializer(serializers.ModelSerializer):
    """Serializer for public estimate viewing"""

    line_items = EstimateLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Estimate
        fields = (
            "estimate_number",
            "title",
            "status",
            "client_name",
            "client_email",
            "client_address_line",
            "client_city",
            "client_state",
            "client_postcode",
            "client_country",
            "subtotal",
            "discount_type",
            "discount_value",
            "discount_amount",
            "tax_rate",
            "tax_amount",
            "total_amount",
            "currency",
            "issue_date",
            "expiry_date",
            "notes",
            "terms",
            "line_items",
        )
