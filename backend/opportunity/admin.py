from django.contrib import admin

from opportunity.models import Opportunity, OpportunityLineItem


class OpportunityLineItemInline(admin.TabularInline):
    model = OpportunityLineItem
    extra = 0
    fields = (
        "product",
        "name",
        "description",
        "quantity",
        "unit_price",
        "discount_type",
        "discount_value",
        "total",
        "order",
    )
    readonly_fields = ("total",)
    autocomplete_fields = ("product",)


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account",
        "stage",
        "amount",
        "amount_source",
        "probability",
        "closed_on",
        "org",
    )
    list_filter = ("stage", "amount_source", "org", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    inlines = [OpportunityLineItemInline]


@admin.register(OpportunityLineItem)
class OpportunityLineItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "opportunity",
        "product",
        "quantity",
        "unit_price",
        "total",
        "org",
    )
    list_filter = ("org", "created_at")
    search_fields = ("name", "description", "opportunity__name")
    ordering = ("-created_at",)
    autocomplete_fields = ("product", "opportunity")
