from django.contrib import admin

from orders.models import Order, OrderLineItem


class OrderLineItemInline(admin.TabularInline):
    model = OrderLineItem
    extra = 1
    fields = (
        "product",
        "name",
        "description",
        "quantity",
        "unit_price",
        "discount_amount",
        "total",
        "sort_order",
    )
    readonly_fields = ("total",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "order_number",
        "account",
        "status",
        "total_amount",
        "order_date",
        "created_at",
    )
    list_filter = ("status", "created_at", "order_date", "org")
    search_fields = (
        "name",
        "order_number",
        "account__name",
    )
    raw_id_fields = (
        "created_by",
        "org",
        "account",
        "contact",
        "opportunity",
    )
    inlines = [OrderLineItemInline]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Order Info",
            {
                "fields": (
                    "name",
                    "order_number",
                    "status",
                )
            },
        ),
        (
            "CRM Integration",
            {
                "fields": (
                    "account",
                    "contact",
                    "opportunity",
                )
            },
        ),
        (
            "Financial",
            {
                "fields": (
                    "currency",
                    "subtotal",
                    "discount_amount",
                    "tax_amount",
                    "total_amount",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "order_date",
                    "activated_date",
                    "shipped_date",
                )
            },
        ),
        (
            "Billing Address",
            {
                "fields": (
                    "billing_address_line",
                    "billing_city",
                    "billing_state",
                    "billing_postcode",
                    "billing_country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Shipping Address",
            {
                "fields": (
                    "shipping_address_line",
                    "shipping_city",
                    "shipping_state",
                    "shipping_postcode",
                    "shipping_country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Notes",
            {
                "fields": ("description",)
            },
        ),
        (
            "Organization",
            {
                "fields": ("org",)
            },
        ),
    )


@admin.register(OrderLineItem)
class OrderLineItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "name",
        "product",
        "quantity",
        "unit_price",
        "discount_amount",
        "total",
        "sort_order",
    )
    list_filter = ("order__status", "created_at")
    search_fields = ("name", "order__name", "product__name")
    raw_id_fields = ("order", "product", "org")
    ordering = ("order", "sort_order")
