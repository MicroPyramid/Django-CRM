from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.serializer import AccountSerializer
from common.serializer import (
    AttachmentsSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    TagsSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer
from invoices.serializer import ProductSerializer
from opportunity.models import Opportunity, OpportunityLineItem


# Note: Removed unused serializer properties that were computed but never used by frontend:
# - get_team_users, get_team_and_assigned_users, get_assigned_users_not_in_teams


class OpportunityLineItemSerializer(serializers.ModelSerializer):
    """Serializer for reading OpportunityLineItem data"""

    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    formatted_unit_price = serializers.SerializerMethodField()
    formatted_total = serializers.SerializerMethodField()

    class Meta:
        model = OpportunityLineItem
        fields = (
            "id",
            "product",
            "product_id",
            "name",
            "description",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "discount_amount",
            "subtotal",
            "total",
            "order",
            "formatted_unit_price",
            "formatted_total",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "discount_amount",
            "subtotal",
            "total",
            "created_at",
            "updated_at",
        )

    def get_formatted_unit_price(self, obj):
        """Format unit price with currency symbol"""
        currency = obj.opportunity.currency or "USD"
        return f"{currency} {obj.unit_price:,.2f}"

    def get_formatted_total(self, obj):
        """Format total with currency symbol"""
        currency = obj.opportunity.currency or "USD"
        return f"{currency} {obj.total:,.2f}"


class OpportunityLineItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating OpportunityLineItem data"""

    product_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = OpportunityLineItem
        fields = (
            "product_id",
            "name",
            "description",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "order",
        )

    def create(self, validated_data):
        # Handle product_id
        product_id = validated_data.pop("product_id", None)
        if product_id:
            from invoices.models import Product

            try:
                validated_data["product"] = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                pass

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle product_id
        product_id = validated_data.pop("product_id", None)
        if product_id:
            from invoices.models import Product

            try:
                validated_data["product"] = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                pass
        elif product_id is None and "product_id" in self.initial_data:
            # Explicitly set to null
            validated_data["product"] = None

        return super().update(instance, validated_data)


class OpportunitySerializer(serializers.ModelSerializer):
    """Serializer for reading Opportunity data"""

    account = AccountSerializer()
    closed_by = ProfileSerializer()
    created_by = UserSerializer()
    org = OrganizationSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    line_items = OpportunityLineItemSerializer(read_only=True, many=True)
    created_on_arrow = serializers.SerializerMethodField()
    line_items_total = serializers.SerializerMethodField()

    @extend_schema_field(str)
    def get_created_on_arrow(self, obj):
        return obj.created_on_arrow

    @extend_schema_field(float)
    def get_line_items_total(self, obj):
        """Calculate total from line items"""
        return sum(item.total for item in obj.line_items.all())

    class Meta:
        model = Opportunity
        fields = (
            "id",
            # Core Opportunity Information
            "name",
            "account",
            "stage",
            "opportunity_type",
            # Financial Information
            "currency",
            "amount",
            "amount_source",
            "probability",
            "closed_on",
            # Source & Context
            "lead_source",
            # Relationships
            "contacts",
            # Line Items / Products
            "line_items",
            "line_items_total",
            # Assignment
            "assigned_to",
            "teams",
            "closed_by",
            # Tags
            "tags",
            # Notes
            "description",
            # System
            "created_by",
            "created_at",
            "is_active",
            "org",
            "created_on_arrow",
        )


class OpportunityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Opportunity data"""

    probability = serializers.IntegerField(
        max_value=100, required=False, allow_null=True
    )
    closed_on = serializers.DateField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        if request_obj:
            self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if (
                Opportunity.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Opportunity already exists with this name"
                )
        else:
            if Opportunity.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError(
                    "Opportunity already exists with this name"
                )
        return name

    class Meta:
        model = Opportunity
        fields = (
            # Core Opportunity Information
            "name",
            "account",
            "stage",
            "opportunity_type",
            # Financial Information
            "currency",
            "amount",
            "probability",
            "closed_on",
            # Source & Context
            "lead_source",
            # Notes
            "description",
            # Status
            "is_active",
        )

    def create(self, validated_data):
        # Default currency from org if not provided
        if not validated_data.get("currency"):
            request = self.context.get("request")
            if request and hasattr(request, "profile") and request.profile.org:
                validated_data["currency"] = request.profile.org.default_currency
        return super().create(validated_data)


class OpportunityCreateSwaggerSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField()

    class Meta:
        model = Opportunity
        fields = (
            "name",
            "account",
            "stage",
            "opportunity_type",
            "amount",
            "currency",
            "probability",
            "closed_on",
            "lead_source",
            "description",
            "assigned_to",
            "contacts",
            "teams",
            "tags",
        )


class OpportunityDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


class OpportunityCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
