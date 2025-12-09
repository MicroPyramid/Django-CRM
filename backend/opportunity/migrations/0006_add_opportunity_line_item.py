# Generated migration for OpportunityLineItem model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_initial"),
        ("invoices", "0004_estimate_estimatelineitem_invoicetemplate_payment_and_more"),
        ("opportunity", "0005_add_enterprise_constraints"),
    ]

    operations = [
        # Add amount_source field to Opportunity
        migrations.AddField(
            model_name="opportunity",
            name="amount_source",
            field=models.CharField(
                choices=[
                    ("MANUAL", "Manual"),
                    ("CALCULATED", "Calculated from Products"),
                ],
                default="MANUAL",
                max_length=20,
                verbose_name="Amount Source",
            ),
        ),
        # Create OpportunityLineItem model
        migrations.CreateModel(
            name="OpportunityLineItem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to="common.user",
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to="common.user",
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Item Name"
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True, max_length=500, verbose_name="Description"
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=2,
                        default=1,
                        max_digits=10,
                        verbose_name="Quantity",
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Unit Price",
                    ),
                ),
                (
                    "discount_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PERCENTAGE", "Percentage (%)"),
                            ("FIXED", "Fixed Amount"),
                        ],
                        max_length=20,
                        verbose_name="Discount Type",
                    ),
                ),
                (
                    "discount_value",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Discount Value",
                    ),
                ),
                (
                    "discount_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Discount Amount",
                    ),
                ),
                (
                    "subtotal",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Subtotal",
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Total",
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(default=0, verbose_name="Order"),
                ),
                (
                    "opportunity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="line_items",
                        to="opportunity.opportunity",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="opportunity_line_items",
                        to="invoices.product",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="opportunity_line_items",
                        to="common.org",
                    ),
                ),
            ],
            options={
                "verbose_name": "Opportunity Line Item",
                "verbose_name_plural": "Opportunity Line Items",
                "db_table": "opportunity_line_item",
                "ordering": ["order", "created_at"],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name="opportunitylineitem",
            index=models.Index(
                fields=["opportunity"], name="opportunity__opportu_5e4c7e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="opportunitylineitem",
            index=models.Index(fields=["org"], name="opportunity__org_id_a1b2c3_idx"),
        ),
    ]
