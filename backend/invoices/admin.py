from django.contrib import admin

from invoices.models import Invoice, InvoiceHistory, InvoiceLineItem, Product


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1
    fields = ("product", "description", "quantity", "unit_price", "total", "order")
    readonly_fields = ("total",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "invoice_title",
        "name",
        "status",
        "total_amount",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "created_at", "due_date")
    search_fields = ("invoice_number", "invoice_title", "name", "email")
    raw_id_fields = ("created_by", "org", "from_address", "to_address")
    filter_horizontal = ("assigned_to", "accounts", "teams")
    inlines = [InvoiceLineItemInline]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(InvoiceHistory)
class InvoiceHistoryAdmin(admin.ModelAdmin):
    list_display = ("invoice", "invoice_number", "status", "updated_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("invoice_number", "invoice_title")
    raw_id_fields = ("invoice", "updated_by")
    ordering = ("-created_at",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "price",
        "category",
        "is_active",
        "org",
        "created_at",
    )
    list_filter = ("is_active", "category", "org", "created_at")
    search_fields = ("name", "sku", "description")
    raw_id_fields = ("org",)
    ordering = ("name",)


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "description",
        "product",
        "quantity",
        "unit_price",
        "total",
        "order",
    )
    list_filter = ("invoice__status", "created_at")
    search_fields = ("description", "invoice__invoice_number", "product__name")
    raw_id_fields = ("invoice", "product")
    ordering = ("invoice", "order")
