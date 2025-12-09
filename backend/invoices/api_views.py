from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum, Count
from datetime import timedelta
import datetime
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Attachments, Comment
from common.permissions import HasOrgContext
from common.serializer import AttachmentsSerializer, CommentSerializer
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
from invoices.serializer import (
    EstimateCreateSerializer,
    EstimateLineItemSerializer,
    EstimateListSerializer,
    EstimateSerializer,
    InvoiceCreateSerializer,
    InvoiceHistorySerializer,
    InvoiceLineItemCreateSerializer,
    InvoiceLineItemSerializer,
    InvoiceListSerializer,
    InvoiceSerializer,
    InvoiceTemplateCreateSerializer,
    InvoiceTemplateSerializer,
    PaymentCreateSerializer,
    PaymentSerializer,
    ProductCreateSerializer,
    ProductSerializer,
    RecurringInvoiceCreateSerializer,
    RecurringInvoiceLineItemSerializer,
    RecurringInvoiceListSerializer,
    RecurringInvoiceSerializer,
)
from invoices.pdf import (
    generate_estimate_filename,
    generate_estimate_pdf,
    generate_invoice_filename,
    generate_invoice_pdf,
)
from django.db import transaction
from invoices.tasks import create_invoice_history, send_email, send_invoice_to_client


# =============================================================================
# INVOICE VIEWS
# =============================================================================


class InvoiceListView(APIView, LimitOffsetPagination):
    """List and create invoices"""

    permission_classes = (IsAuthenticated, HasOrgContext)
    model = Invoice

    def get_queryset(self):
        """Get invoices filtered by org and user permissions"""
        org = self.request.profile.org
        role = self.request.profile.role

        queryset = (
            self.model.objects.filter(org=org)
            .select_related("account", "contact", "opportunity", "created_by")
            .prefetch_related("line_items", "payments", "assigned_to")
        )

        # Non-admin users can only see their own or assigned invoices
        if role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()

        return queryset

    def filter_queryset(self, queryset):
        """Apply filters from query params"""
        params = self.request.query_params

        # Search by invoice number or title (limit length to prevent expensive queries)
        search = params.get("search")
        if search:
            search = search[:100]  # Limit search term length
            queryset = queryset.filter(
                Q(invoice_title__icontains=search)
                | Q(invoice_number__icontains=search)
                | Q(client_name__icontains=search)
                | Q(client_email__icontains=search)
            ).distinct()

        # Filter by status
        if params.get("status"):
            queryset = queryset.filter(status=params.get("status"))

        # Filter by account
        if params.get("account"):
            queryset = queryset.filter(account_id=params.get("account"))

        # Filter by contact
        if params.get("contact"):
            queryset = queryset.filter(contact_id=params.get("contact"))

        # Filter by opportunity
        if params.get("opportunity"):
            queryset = queryset.filter(opportunity_id=params.get("opportunity"))

        # Filter by assigned user
        if params.get("assigned_to"):
            queryset = queryset.filter(assigned_to__id=params.get("assigned_to"))

        # Filter by created_by
        if params.get("created_by"):
            queryset = queryset.filter(created_by__id=params.get("created_by"))

        # Filter by date range
        if params.get("issue_date_gte"):
            queryset = queryset.filter(issue_date__gte=params.get("issue_date_gte"))
        if params.get("issue_date_lte"):
            queryset = queryset.filter(issue_date__lte=params.get("issue_date_lte"))
        if params.get("due_date_gte"):
            queryset = queryset.filter(due_date__gte=params.get("due_date_gte"))
        if params.get("due_date_lte"):
            queryset = queryset.filter(due_date__lte=params.get("due_date_lte"))

        # Sorting
        sort = params.get("sort", "-created_at")
        if sort.lstrip("-") in [
            "created_at",
            "due_date",
            "issue_date",
            "total_amount",
            "status",
        ]:
            queryset = queryset.order_by(sort)

        return queryset

    @extend_schema(tags=["Invoices"], operation_id="invoices_list")
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        results = self.paginate_queryset(queryset, request, view=self)
        serializer = InvoiceListSerializer(results, many=True)

        return Response(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": serializer.data,
            }
        )

    @extend_schema(tags=["Invoices"], operation_id="invoices_create")
    def post(self, request, *args, **kwargs):
        serializer = InvoiceCreateSerializer(
            data=request.data, request_obj=request, context={"request": request}
        )

        if serializer.is_valid():
            invoice = serializer.save()

            # Create history entry
            create_invoice_history.delay(
                str(invoice.id),
                str(request.profile.id),
                [],
                str(request.profile.org.id),
            )

            # Send notification email to assigned users
            assigned_to_ids = list(invoice.assigned_to.values_list("id", flat=True))
            if assigned_to_ids:
                send_email.delay(
                    str(invoice.id),
                    [str(uid) for uid in assigned_to_ids],
                    str(request.profile.org.id),
                    domain=getattr(settings, "DOMAIN_NAME", "localhost"),
                    protocol=request.scheme,
                )

            return Response(
                {
                    "error": False,
                    "message": "Invoice created successfully",
                    "invoice": InvoiceSerializer(invoice).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceDetailView(APIView):
    """Retrieve and update a single invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)
    model = Invoice

    def get_object(self, pk):
        return self.model.objects.filter(id=pk, org=self.request.profile.org).first()

    def check_permissions_for_object(self, invoice):
        """Check if user has permission to access this invoice"""
        role = self.request.profile.role
        if role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                self.request.profile == invoice.created_by
                or self.request.profile in invoice.assigned_to.all()
            ):
                return False
        return True

    @extend_schema(tags=["Invoices"], operation_id="invoices_retrieve")
    def get(self, request, pk, format=None):
        invoice = self.get_object(pk)
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not self.check_permissions_for_object(invoice):
            return Response(
                {"error": True, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get attachments and comments
        invoice_content_type = ContentType.objects.get_for_model(Invoice)
        attachments = Attachments.objects.filter(
            content_type=invoice_content_type,
            object_id=invoice.id,
            org=request.profile.org,
        ).order_by("-id")
        comments = Comment.objects.filter(
            content_type=invoice_content_type,
            object_id=invoice.id,
            org=request.profile.org,
        ).order_by("-id")

        return Response(
            {
                "invoice": InvoiceSerializer(invoice).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "history": InvoiceHistorySerializer(
                    invoice.invoice_history.all(), many=True
                ).data,
            }
        )

    @extend_schema(tags=["Invoices"], operation_id="invoices_update")
    def put(self, request, pk, format=None):
        invoice = self.get_object(pk)
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not self.check_permissions_for_object(invoice):
            return Response(
                {"error": True, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = InvoiceCreateSerializer(
            invoice,
            data=request.data,
            request_obj=request,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            invoice = serializer.save()

            # Create history entry
            create_invoice_history.delay(
                str(invoice.id),
                str(request.profile.id),
                [],
                str(request.profile.org.id),
            )

            return Response(
                {
                    "error": False,
                    "message": "Invoice updated successfully",
                    "invoice": InvoiceSerializer(invoice).data,
                }
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceSendView(APIView):
    """Send invoice to client via email"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoices"], operation_id="invoices_send")
    def post(self, request, pk):
        invoice = Invoice.objects.filter(id=pk, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update status and sent_at
        if invoice.status == "Draft":
            invoice.status = "Sent"
        invoice.sent_at = timezone.now()
        invoice.is_email_sent = True
        invoice.save()

        # Send invoice email to client
        send_invoice_to_client.delay(
            str(invoice.id),
            str(request.profile.org.id),
            domain=getattr(settings, "DOMAIN_NAME", "localhost"),
            protocol=request.scheme,
        )

        return Response({"error": False, "message": "Invoice sent successfully"})


class InvoiceMarkPaidView(APIView):
    """Mark invoice as paid"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoices"], operation_id="invoices_mark_paid")
    def post(self, request, pk):
        invoice = Invoice.objects.filter(id=pk, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create payment record if amount provided
        amount = request.data.get("amount", invoice.amount_due)
        payment_method = request.data.get("payment_method", "OTHER")
        payment_date = request.data.get("payment_date", timezone.now().date())

        Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            reference_number=request.data.get("reference_number", ""),
            notes=request.data.get("notes", ""),
            org=request.profile.org,
        )

        # Refresh invoice from DB to get updated payment totals
        invoice.refresh_from_db()

        return Response(
            {
                "error": False,
                "message": "Payment recorded successfully",
                "invoice": InvoiceSerializer(invoice).data,
            }
        )


class InvoiceDuplicateView(APIView):
    """Duplicate an existing invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoices"], operation_id="invoices_duplicate")
    def post(self, request, pk):
        original = Invoice.objects.filter(id=pk, org=request.profile.org).first()
        if not original:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            # Create duplicate invoice
            new_invoice = Invoice.objects.create(
                invoice_title=f"Copy of {original.invoice_title}",
                status="Draft",
                account=original.account,
                contact=original.contact,
                opportunity=original.opportunity,
                client_name=original.client_name,
                client_email=original.client_email,
                client_phone=original.client_phone,
                billing_address_line=original.billing_address_line,
                billing_city=original.billing_city,
                billing_state=original.billing_state,
                billing_postcode=original.billing_postcode,
                billing_country=original.billing_country,
                client_address_line=original.client_address_line,
                client_city=original.client_city,
                client_state=original.client_state,
                client_postcode=original.client_postcode,
                client_country=original.client_country,
                discount_type=original.discount_type,
                discount_value=original.discount_value,
                tax_rate=original.tax_rate,
                shipping_amount=original.shipping_amount,
                currency=original.currency,
                issue_date=timezone.now().date(),
                payment_terms=original.payment_terms,
                reminder_enabled=original.reminder_enabled,
                reminder_days_before=original.reminder_days_before,
                reminder_days_after=original.reminder_days_after,
                reminder_frequency=original.reminder_frequency,
                template=original.template,
                notes=original.notes,
                terms=original.terms,
                org=request.profile.org,
            )

            # Copy line items
            for item in original.line_items.all():
                InvoiceLineItem.objects.create(
                    invoice=new_invoice,
                    product=item.product,
                    name=item.name,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_type=item.discount_type,
                    discount_value=item.discount_value,
                    tax_rate=item.tax_rate,
                    order=item.order,
                    org=request.profile.org,
                )

            # Recalculate totals
            new_invoice.recalculate_totals()
            new_invoice.save()

            return Response(
                {
                    "error": False,
                    "message": "Invoice duplicated successfully",
                    "invoice": InvoiceSerializer(new_invoice).data,
                },
                status=status.HTTP_201_CREATED,
            )


class InvoiceCancelView(APIView):
    """Cancel an invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoices"], operation_id="invoices_cancel")
    def post(self, request, pk):
        invoice = Invoice.objects.filter(id=pk, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        role = request.profile.role
        if role != "ADMIN" and not request.user.is_superuser:
            if not (
                request.profile == invoice.created_by
                or request.profile in invoice.assigned_to.all()
            ):
                return Response(
                    {"error": True, "message": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Cannot cancel already cancelled invoices
        if invoice.status == "Cancelled":
            return Response(
                {"error": True, "message": "Invoice is already cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cannot cancel paid invoices
        if invoice.status == "Paid":
            return Response(
                {"error": True, "message": "Cannot cancel a paid invoice"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cancel the invoice
        invoice.status = "Cancelled"
        invoice.cancelled_at = timezone.now()
        invoice.save(update_fields=["status", "cancelled_at"])

        return Response(
            {
                "error": False,
                "message": "Invoice cancelled successfully",
                "invoice": InvoiceSerializer(invoice).data,
            }
        )


class InvoicePDFView(APIView):
    """Generate and download invoice PDF"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoices"], operation_id="invoices_pdf")
    def get(self, request, pk):
        invoice = Invoice.objects.filter(id=pk, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check user permissions
        role = request.profile.role
        if role != "ADMIN" and not request.user.is_superuser:
            if not (
                request.profile == invoice.created_by
                or request.profile in invoice.assigned_to.all()
            ):
                return Response(
                    {"error": True, "message": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            pdf_content = generate_invoice_pdf(invoice)
            filename = generate_invoice_filename(invoice)

            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except ImportError as e:
            return Response(
                {"error": True, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"error": True, "message": f"Error generating PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# =============================================================================
# LINE ITEM VIEWS
# =============================================================================


class InvoiceLineItemListView(APIView):
    """Manage line items for an invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_invoice(self, invoice_id):
        return Invoice.objects.filter(
            id=invoice_id, org=self.request.profile.org
        ).first()

    @extend_schema(tags=["Invoice Line Items"], operation_id="line_items_list")
    def get(self, request, invoice_id):
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        line_items = invoice.line_items.all().order_by("order")
        return Response(InvoiceLineItemSerializer(line_items, many=True).data)

    @extend_schema(tags=["Invoice Line Items"], operation_id="line_items_create")
    def post(self, request, invoice_id):
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InvoiceLineItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            line_item = serializer.save(invoice=invoice, org=request.profile.org)

            # Recalculate invoice totals
            invoice.recalculate_totals()
            invoice.save()

            return Response(
                {
                    "error": False,
                    "message": "Line item added",
                    "line_item": InvoiceLineItemSerializer(line_item).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceLineItemDetailView(APIView):
    """Update or delete a single line item"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, invoice_id, pk):
        return InvoiceLineItem.objects.filter(
            id=pk, invoice_id=invoice_id, org=self.request.profile.org
        ).first()

    @extend_schema(tags=["Invoice Line Items"], operation_id="line_items_update")
    def put(self, request, invoice_id, pk):
        line_item = self.get_object(invoice_id, pk)
        if not line_item:
            return Response(
                {"error": True, "message": "Line item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InvoiceLineItemCreateSerializer(
            line_item, data=request.data, partial=True
        )
        if serializer.is_valid():
            line_item = serializer.save()

            # Recalculate invoice totals
            line_item.invoice.recalculate_totals()
            line_item.invoice.save()

            return Response(
                {
                    "error": False,
                    "message": "Line item updated",
                    "line_item": InvoiceLineItemSerializer(line_item).data,
                }
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Invoice Line Items"], operation_id="line_items_destroy")
    def delete(self, request, invoice_id, pk):
        line_item = self.get_object(invoice_id, pk)
        if not line_item:
            return Response(
                {"error": True, "message": "Line item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        invoice = line_item.invoice
        line_item.delete()

        # Recalculate invoice totals
        invoice.recalculate_totals()
        invoice.save()

        return Response(
            {"error": False, "message": "Line item deleted"},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# PAYMENT VIEWS
# =============================================================================


class PaymentListView(APIView, LimitOffsetPagination):
    """List and create payments for an invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Payments"], operation_id="payments_list")
    def get(self, request, invoice_id):
        invoice = Invoice.objects.filter(id=invoice_id, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        payments = invoice.payments.all().order_by("-payment_date")
        return Response(PaymentSerializer(payments, many=True).data)

    @extend_schema(tags=["Payments"], operation_id="payments_create")
    def post(self, request, invoice_id):
        invoice = Invoice.objects.filter(id=invoice_id, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(invoice=invoice, org=request.profile.org)
            return Response(
                {
                    "error": False,
                    "message": "Payment recorded",
                    "payment": PaymentSerializer(payment).data,
                    "invoice": InvoiceListSerializer(invoice).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PaymentDetailView(APIView):
    """Delete a payment"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Payments"], operation_id="payments_destroy")
    def delete(self, request, invoice_id, pk):
        payment = (
            Payment.objects.filter(
                id=pk, invoice_id=invoice_id, org=request.profile.org
            )
            .select_related("invoice")
            .first()
        )
        if not payment:
            return Response(
                {"error": True, "message": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check user permissions - must be admin, invoice creator, or assigned to invoice
        invoice = payment.invoice
        role = request.profile.role
        if role != "ADMIN" and not request.user.is_superuser:
            if not (
                request.profile == invoice.created_by
                or request.profile in invoice.assigned_to.all()
            ):
                return Response(
                    {"error": True, "message": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        payment.delete()
        return Response(
            {"error": False, "message": "Payment deleted"},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# PRODUCT VIEWS
# =============================================================================


class ProductListView(APIView, LimitOffsetPagination):
    """List and create products"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Products"], operation_id="products_list")
    def get(self, request):
        queryset = Product.objects.filter(org=request.profile.org)

        # Filter by active status
        if request.query_params.get("is_active"):
            is_active = request.query_params.get("is_active").lower() == "true"
            queryset = queryset.filter(is_active=is_active)

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(sku__icontains=search)
                | Q(description__icontains=search)
            )

        # Category filter
        if request.query_params.get("category"):
            queryset = queryset.filter(category=request.query_params.get("category"))

        results = self.paginate_queryset(queryset.order_by("name"), request, view=self)
        return Response(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": ProductSerializer(results, many=True).data,
            }
        )

    @extend_schema(tags=["Products"], operation_id="products_create")
    def post(self, request):
        serializer = ProductCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            product = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Product created",
                    "product": ProductSerializer(product).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProductDetailView(APIView):
    """Retrieve, update, and delete a product"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return Product.objects.filter(id=pk, org=self.request.profile.org).first()

    @extend_schema(tags=["Products"], operation_id="products_retrieve")
    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"error": True, "message": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ProductSerializer(product).data)

    @extend_schema(tags=["Products"], operation_id="products_update")
    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"error": True, "message": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductCreateSerializer(
            product, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            product = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Product updated",
                    "product": ProductSerializer(product).data,
                }
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Products"], operation_id="products_destroy")
    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"error": True, "message": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        product.delete()
        return Response(
            {"error": False, "message": "Product deleted"},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# ESTIMATE VIEWS
# =============================================================================


class EstimateListView(APIView, LimitOffsetPagination):
    """List and create estimates"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_queryset(self):
        org = self.request.profile.org
        role = self.request.profile.role

        queryset = Estimate.objects.filter(org=org).select_related(
            "account", "contact", "opportunity", "created_by"
        )

        if role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.profile) | Q(assigned_to=self.request.profile)
            ).distinct()

        return queryset

    @extend_schema(tags=["Estimates"], operation_id="estimates_list")
    def get(self, request):
        queryset = self.get_queryset()

        # Apply filters
        params = request.query_params
        if params.get("status"):
            queryset = queryset.filter(status=params.get("status"))
        if params.get("account"):
            queryset = queryset.filter(account_id=params.get("account"))
        if params.get("search"):
            search = params.get("search")
            queryset = queryset.filter(
                Q(estimate_number__icontains=search)
                | Q(title__icontains=search)
                | Q(client_name__icontains=search)
            )

        results = self.paginate_queryset(
            queryset.order_by("-created_at"), request, view=self
        )
        return Response(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": EstimateListSerializer(results, many=True).data,
            }
        )

    @extend_schema(tags=["Estimates"], operation_id="estimates_create")
    def post(self, request):
        serializer = EstimateCreateSerializer(
            data=request.data, request_obj=request, context={"request": request}
        )
        if serializer.is_valid():
            estimate = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Estimate created",
                    "estimate": EstimateSerializer(estimate).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class EstimateDetailView(APIView):
    """Retrieve, update, and delete an estimate"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return Estimate.objects.filter(id=pk, org=self.request.profile.org).first()

    @extend_schema(tags=["Estimates"], operation_id="estimates_retrieve")
    def get(self, request, pk):
        estimate = self.get_object(pk)
        if not estimate:
            return Response(
                {"error": True, "message": "Estimate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"estimate": EstimateSerializer(estimate).data})

    @extend_schema(tags=["Estimates"], operation_id="estimates_update")
    def put(self, request, pk):
        estimate = self.get_object(pk)
        if not estimate:
            return Response(
                {"error": True, "message": "Estimate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EstimateCreateSerializer(
            estimate,
            data=request.data,
            request_obj=request,
            context={"request": request},
            partial=True,
        )
        if serializer.is_valid():
            estimate = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Estimate updated",
                    "estimate": EstimateSerializer(estimate).data,
                }
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Estimates"], operation_id="estimates_destroy")
    def delete(self, request, pk):
        estimate = self.get_object(pk)
        if not estimate:
            return Response(
                {"error": True, "message": "Estimate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        estimate.delete()
        return Response(
            {"error": False, "message": "Estimate deleted"},
            status=status.HTTP_200_OK,
        )


class EstimateConvertView(APIView):
    """Convert an estimate to an invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Estimates"], operation_id="estimates_convert")
    def post(self, request, pk):
        estimate = Estimate.objects.filter(id=pk, org=request.profile.org).first()
        if not estimate:
            return Response(
                {"error": True, "message": "Estimate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if estimate.converted_to_invoice:
            return Response(
                {"error": True, "message": "Estimate already converted to invoice"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Create invoice from estimate
            invoice = Invoice.objects.create(
                invoice_title=estimate.title,
                status="Draft",
                account=estimate.account,
                contact=estimate.contact,
                opportunity=estimate.opportunity,
                client_name=estimate.client_name,
                client_email=estimate.client_email,
                client_phone=estimate.client_phone,
                client_address_line=estimate.client_address_line,
                client_city=estimate.client_city,
                client_state=estimate.client_state,
                client_postcode=estimate.client_postcode,
                client_country=estimate.client_country,
                subtotal=estimate.subtotal,
                discount_type=estimate.discount_type,
                discount_value=estimate.discount_value,
                tax_rate=estimate.tax_rate,
                currency=estimate.currency,
                issue_date=timezone.now().date(),
                notes=estimate.notes,
                terms=estimate.terms,
                org=request.profile.org,
            )

            # Copy line items
            for item in estimate.line_items.all():
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product=item.product,
                    name=item.name,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_type=item.discount_type,
                    discount_value=item.discount_value,
                    tax_rate=item.tax_rate,
                    order=item.order,
                    org=request.profile.org,
                )

            # Recalculate totals
            invoice.recalculate_totals()
            invoice.save()

            # Update estimate
            estimate.status = "Accepted"
            estimate.accepted_at = timezone.now()
            estimate.converted_to_invoice = invoice
            estimate.save()

        return Response(
            {
                "error": False,
                "message": "Estimate converted to invoice",
                "invoice": InvoiceSerializer(invoice).data,
            },
            status=status.HTTP_201_CREATED,
        )


class EstimateSendView(APIView):
    """Send estimate to client via email"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Estimates"], operation_id="estimates_send")
    def post(self, request, pk):
        estimate = Estimate.objects.filter(id=pk, org=request.profile.org).first()
        if not estimate:
            return Response(
                {"error": True, "message": "Estimate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update status and sent_at
        if estimate.status == "Draft":
            estimate.status = "Sent"
        estimate.sent_at = timezone.now()
        estimate.save()

        # Trigger async email task
        from invoices.tasks import send_estimate_to_client

        send_estimate_to_client.delay(str(estimate.id), str(request.profile.org.id))

        return Response({"error": False, "message": "Estimate sent successfully"})


class EstimatePDFView(APIView):
    """Generate and download estimate PDF"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Estimates"], operation_id="estimates_pdf")
    def get(self, request, pk):
        estimate = Estimate.objects.filter(id=pk, org=request.profile.org).first()
        if not estimate:
            return Response(
                {"error": True, "message": "Estimate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check user permissions
        role = request.profile.role
        if role != "ADMIN" and not request.user.is_superuser:
            if not (
                request.profile == estimate.created_by
                or request.profile in estimate.assigned_to.all()
            ):
                return Response(
                    {"error": True, "message": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            pdf_content = generate_estimate_pdf(estimate)
            filename = generate_estimate_filename(estimate)

            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except ImportError as e:
            return Response(
                {"error": True, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"error": True, "message": f"Error generating PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# =============================================================================
# RECURRING INVOICE VIEWS
# =============================================================================


class RecurringInvoiceListView(APIView, LimitOffsetPagination):
    """List and create recurring invoices"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Recurring Invoices"], operation_id="recurring_list")
    def get(self, request):
        queryset = (
            RecurringInvoice.objects.filter(org=request.profile.org)
            .select_related("account", "contact")
            .order_by("-created_at")
        )

        # Apply filters
        if request.query_params.get("is_active"):
            is_active = request.query_params.get("is_active").lower() == "true"
            queryset = queryset.filter(is_active=is_active)

        results = self.paginate_queryset(queryset, request, view=self)
        return Response(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": RecurringInvoiceListSerializer(results, many=True).data,
            }
        )

    @extend_schema(tags=["Recurring Invoices"], operation_id="recurring_create")
    def post(self, request):
        serializer = RecurringInvoiceCreateSerializer(
            data=request.data, request_obj=request, context={"request": request}
        )
        if serializer.is_valid():
            recurring = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Recurring invoice created",
                    "recurring_invoice": RecurringInvoiceSerializer(recurring).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RecurringInvoiceDetailView(APIView):
    """Retrieve, update, and delete a recurring invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return RecurringInvoice.objects.filter(
            id=pk, org=self.request.profile.org
        ).first()

    @extend_schema(tags=["Recurring Invoices"], operation_id="recurring_retrieve")
    def get(self, request, pk):
        recurring = self.get_object(pk)
        if not recurring:
            return Response(
                {"error": True, "message": "Recurring invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(RecurringInvoiceSerializer(recurring).data)

    @extend_schema(tags=["Recurring Invoices"], operation_id="recurring_update")
    def put(self, request, pk):
        recurring = self.get_object(pk)
        if not recurring:
            return Response(
                {"error": True, "message": "Recurring invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RecurringInvoiceCreateSerializer(
            recurring,
            data=request.data,
            request_obj=request,
            context={"request": request},
            partial=True,
        )
        if serializer.is_valid():
            recurring = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Recurring invoice updated",
                    "recurring_invoice": RecurringInvoiceSerializer(recurring).data,
                }
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Recurring Invoices"], operation_id="recurring_destroy")
    def delete(self, request, pk):
        recurring = self.get_object(pk)
        if not recurring:
            return Response(
                {"error": True, "message": "Recurring invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        recurring.delete()
        return Response(
            {"error": False, "message": "Recurring invoice deleted"},
            status=status.HTTP_200_OK,
        )


class RecurringInvoicePauseView(APIView):
    """Pause or resume a recurring invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Recurring Invoices"], operation_id="recurring_toggle")
    def post(self, request, pk):
        recurring = RecurringInvoice.objects.filter(
            id=pk, org=request.profile.org
        ).first()
        if not recurring:
            return Response(
                {"error": True, "message": "Recurring invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        recurring.is_active = not recurring.is_active
        recurring.save()

        action = "resumed" if recurring.is_active else "paused"
        return Response(
            {
                "error": False,
                "message": f"Recurring invoice {action}",
                "recurring_invoice": RecurringInvoiceListSerializer(recurring).data,
            }
        )


# =============================================================================
# INVOICE TEMPLATE VIEWS
# =============================================================================


class InvoiceTemplateListView(APIView, LimitOffsetPagination):
    """List and create invoice templates"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoice Templates"], operation_id="templates_list")
    def get(self, request):
        queryset = InvoiceTemplate.objects.filter(org=request.profile.org).order_by(
            "-is_default", "name"
        )

        results = self.paginate_queryset(queryset, request, view=self)
        return Response(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": InvoiceTemplateSerializer(results, many=True).data,
            }
        )

    @extend_schema(tags=["Invoice Templates"], operation_id="templates_create")
    def post(self, request):
        serializer = InvoiceTemplateCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            template = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Template created",
                    "template": InvoiceTemplateSerializer(template).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceTemplateDetailView(APIView):
    """Retrieve, update, and delete an invoice template"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return InvoiceTemplate.objects.filter(
            id=pk, org=self.request.profile.org
        ).first()

    @extend_schema(tags=["Invoice Templates"], operation_id="templates_retrieve")
    def get(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response(
                {"error": True, "message": "Template not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(InvoiceTemplateSerializer(template).data)

    @extend_schema(tags=["Invoice Templates"], operation_id="templates_update")
    def put(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response(
                {"error": True, "message": "Template not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InvoiceTemplateCreateSerializer(
            template, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            template = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "Template updated",
                    "template": InvoiceTemplateSerializer(template).data,
                }
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Invoice Templates"], operation_id="templates_destroy")
    def delete(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response(
                {"error": True, "message": "Template not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        template.delete()
        return Response(
            {"error": False, "message": "Template deleted"},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# COMMENTS AND ATTACHMENTS
# =============================================================================


class InvoiceCommentView(APIView):
    """Manage comments on an invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoice Comments"], operation_id="comments_create")
    def post(self, request, invoice_id):
        invoice = Invoice.objects.filter(id=invoice_id, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        comment_text = request.data.get("comment")
        if not comment_text:
            return Response(
                {"error": True, "message": "Comment text required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_content_type = ContentType.objects.get_for_model(Invoice)
        comment = Comment.objects.create(
            content_type=invoice_content_type,
            object_id=invoice.id,
            comment=comment_text,
            commented_by=request.profile,
            org=request.profile.org,
        )

        return Response(
            {
                "error": False,
                "message": "Comment added",
                "comment": CommentSerializer(comment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class InvoiceCommentDetailView(APIView):
    """Update or delete a comment"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return Comment.objects.filter(id=pk, org=self.request.profile.org).first()

    @extend_schema(tags=["Invoice Comments"], operation_id="comments_update")
    def put(self, request, pk):
        comment = self.get_object(pk)
        if not comment:
            return Response(
                {"error": True, "message": "Comment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only comment author or admin can edit
        role = request.profile.role
        if comment.commented_by != request.profile and role != "ADMIN":
            return Response(
                {"error": True, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        comment.comment = request.data.get("comment", comment.comment)
        comment.save()

        return Response(
            {
                "error": False,
                "message": "Comment updated",
                "comment": CommentSerializer(comment).data,
            }
        )

    @extend_schema(tags=["Invoice Comments"], operation_id="comments_destroy")
    def delete(self, request, pk):
        comment = self.get_object(pk)
        if not comment:
            return Response(
                {"error": True, "message": "Comment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = request.profile.role
        if comment.commented_by != request.profile and role != "ADMIN":
            return Response(
                {"error": True, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        comment.delete()
        return Response(
            {"error": False, "message": "Comment deleted"},
            status=status.HTTP_200_OK,
        )


class InvoiceAttachmentView(APIView):
    """Manage attachments on an invoice"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoice Attachments"], operation_id="attachments_create")
    def post(self, request, invoice_id):
        invoice = Invoice.objects.filter(id=invoice_id, org=request.profile.org).first()
        if not invoice:
            return Response(
                {"error": True, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not request.FILES.get("file"):
            return Response(
                {"error": True, "message": "File required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_content_type = ContentType.objects.get_for_model(Invoice)
        attachment = Attachments.objects.create(
            content_type=invoice_content_type,
            object_id=invoice.id,
            file_name=request.FILES.get("file").name,
            attachment=request.FILES.get("file"),
            created_by=request.profile,
            org=request.profile.org,
        )

        return Response(
            {
                "error": False,
                "message": "Attachment uploaded",
                "attachment": AttachmentsSerializer(attachment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class InvoiceAttachmentDetailView(APIView):
    """Delete an attachment"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Invoice Attachments"], operation_id="attachments_destroy")
    def delete(self, request, pk):
        attachment = Attachments.objects.filter(id=pk, org=request.profile.org).first()
        if not attachment:
            return Response(
                {"error": True, "message": "Attachment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = request.profile.role
        if attachment.created_by != request.profile and role != "ADMIN":
            return Response(
                {"error": True, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        attachment.delete()
        return Response(
            {"error": False, "message": "Attachment deleted"},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# REPORTS AND DASHBOARD VIEWS
# =============================================================================


class InvoiceDashboardView(APIView):
    """Dashboard summary for invoices"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Reports"], operation_id="dashboard")
    def get(self, request):
        org = request.profile.org
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        # Total invoices
        all_invoices = Invoice.objects.filter(org=org)

        # Status counts
        status_counts = (
            all_invoices.values("status").annotate(count=Count("id")).order_by("status")
        )

        # Financial summary
        totals = all_invoices.aggregate(
            total_invoiced=Sum("total_amount"),
            total_paid=Sum("amount_paid"),
            total_due=Sum("amount_due"),
        )

        # Overdue invoices
        overdue_invoices = all_invoices.filter(
            status__in=["Sent", "Viewed", "Partially_Paid"],
            due_date__lt=today,
        )
        overdue_count = overdue_invoices.count()
        overdue_amount = (
            overdue_invoices.aggregate(total=Sum("amount_due"))["total"] or 0
        )

        # Recent activity (last 30 days)
        recent_invoices = all_invoices.filter(created_at__gte=thirty_days_ago)
        recent_paid = all_invoices.filter(paid_at__gte=thirty_days_ago)

        recent_revenue = recent_paid.aggregate(total=Sum("amount_paid"))["total"] or 0
        recent_invoiced = (
            recent_invoices.aggregate(total=Sum("total_amount"))["total"] or 0
        )

        # Estimates summary
        all_estimates = Estimate.objects.filter(org=org)
        estimates_pending = all_estimates.filter(status__in=["Sent", "Viewed"]).count()
        estimates_accepted = all_estimates.filter(status="Accepted").count()
        estimates_declined = all_estimates.filter(status="Declined").count()

        return Response(
            {
                "summary": {
                    "total_invoiced": str(totals["total_invoiced"] or 0),
                    "total_paid": str(totals["total_paid"] or 0),
                    "total_due": str(totals["total_due"] or 0),
                },
                "status_counts": {
                    item["status"]: item["count"] for item in status_counts
                },
                "overdue": {
                    "count": overdue_count,
                    "amount": str(overdue_amount),
                },
                "recent_activity": {
                    "revenue_30d": str(recent_revenue),
                    "invoiced_30d": str(recent_invoiced),
                    "invoices_created_30d": recent_invoices.count(),
                    "invoices_paid_30d": recent_paid.count(),
                },
                "estimates": {
                    "pending": estimates_pending,
                    "accepted": estimates_accepted,
                    "declined": estimates_declined,
                },
            }
        )


class RevenueReportView(APIView):
    """Revenue report with date range and grouping"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Reports"], operation_id="revenue_report")
    def get(self, request):
        org = request.profile.org

        # Date range filters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        group_by = request.GET.get("group_by", "month")  # day, week, month, year

        if not start_date:
            start_date = (timezone.now() - timedelta(days=365)).date()
        else:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        # Get paid invoices in date range
        paid_invoices = Invoice.objects.filter(
            org=org,
            paid_at__date__gte=start_date,
            paid_at__date__lte=end_date,
        )

        # Group revenue
        if group_by == "day":
            from django.db.models.functions import TruncDay

            grouped = (
                paid_invoices.annotate(period=TruncDay("paid_at"))
                .values("period")
                .annotate(
                    revenue=Sum("amount_paid"),
                    count=Count("id"),
                )
                .order_by("period")
            )
        elif group_by == "week":
            from django.db.models.functions import TruncWeek

            grouped = (
                paid_invoices.annotate(period=TruncWeek("paid_at"))
                .values("period")
                .annotate(
                    revenue=Sum("amount_paid"),
                    count=Count("id"),
                )
                .order_by("period")
            )
        elif group_by == "year":
            from django.db.models.functions import TruncYear

            grouped = (
                paid_invoices.annotate(period=TruncYear("paid_at"))
                .values("period")
                .annotate(
                    revenue=Sum("amount_paid"),
                    count=Count("id"),
                )
                .order_by("period")
            )
        else:  # month (default)
            from django.db.models.functions import TruncMonth

            grouped = (
                paid_invoices.annotate(period=TruncMonth("paid_at"))
                .values("period")
                .annotate(
                    revenue=Sum("amount_paid"),
                    count=Count("id"),
                )
                .order_by("period")
            )

        # Format results
        data = [
            {
                "period": item["period"].strftime("%Y-%m-%d")
                if item["period"]
                else None,
                "revenue": str(item["revenue"] or 0),
                "count": item["count"],
            }
            for item in grouped
        ]

        # Total
        total = paid_invoices.aggregate(
            revenue=Sum("amount_paid"),
            count=Count("id"),
        )

        return Response(
            {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "group_by": group_by,
                "data": data,
                "total": {
                    "revenue": str(total["revenue"] or 0),
                    "count": total["count"],
                },
            }
        )


class AgingReportView(APIView):
    """Accounts receivable aging report"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Reports"], operation_id="aging_report")
    def get(self, request):
        org = request.profile.org
        today = timezone.now().date()

        # Get unpaid invoices
        unpaid_invoices = Invoice.objects.filter(
            org=org,
            status__in=["Sent", "Viewed", "Partially_Paid", "Overdue"],
            amount_due__gt=0,
        )

        # Categorize by age
        current = []  # Not yet due
        days_1_30 = []
        days_31_60 = []
        days_61_90 = []
        over_90 = []

        for invoice in unpaid_invoices:
            if not invoice.due_date:
                current.append(invoice)
                continue

            days_overdue = (today - invoice.due_date).days

            if days_overdue <= 0:
                current.append(invoice)
            elif days_overdue <= 30:
                days_1_30.append(invoice)
            elif days_overdue <= 60:
                days_31_60.append(invoice)
            elif days_overdue <= 90:
                days_61_90.append(invoice)
            else:
                over_90.append(invoice)

        def summarize(invoices):
            total = sum((inv.amount_due or Decimal("0")) for inv in invoices)
            return {
                "count": len(invoices),
                "amount": str(total),
                "invoices": [
                    {
                        "id": str(inv.id),
                        "invoice_number": inv.invoice_number,
                        "client_name": inv.client_name,
                        "due_date": str(inv.due_date) if inv.due_date else None,
                        "amount_due": str(inv.amount_due),
                        "days_overdue": (today - inv.due_date).days
                        if inv.due_date
                        else 0,
                    }
                    for inv in invoices[:10]  # Limit to 10 per category
                ],
            }

        return Response(
            {
                "current": summarize(current),
                "1_30_days": summarize(days_1_30),
                "31_60_days": summarize(days_31_60),
                "61_90_days": summarize(days_61_90),
                "over_90_days": summarize(over_90),
                "total": {
                    "count": unpaid_invoices.count(),
                    "amount": str(
                        sum((inv.amount_due or Decimal("0")) for inv in unpaid_invoices)
                    ),
                },
            }
        )


# =============================================================================
# INVOICE FROM OPPORTUNITY
# =============================================================================


class InvoiceFromOpportunityView(APIView):
    """
    Create an invoice from a won opportunity.
    Copies all line items from the opportunity to the new invoice.
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        operation_id="invoice_from_opportunity",
        tags=["Invoices"],
        description="Create an invoice from a CLOSED_WON opportunity with line items",
        responses={
            201: InvoiceSerializer(),
            400: {"description": "Bad request - opportunity not won or no line items"},
            404: {"description": "Opportunity not found"},
        },
    )
    def post(self, request, opportunity_id, *args, **kwargs):
        """Create invoice from opportunity"""
        from opportunity.models import Opportunity

        org = request.profile.org

        # Get the opportunity
        opportunity = (
            Opportunity.objects.filter(id=opportunity_id, org=org)
            .prefetch_related("line_items", "contacts")
            .first()
        )

        if not opportunity:
            return Response(
                {"error": True, "message": "Opportunity not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permission
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            if not (
                (request.profile.user == opportunity.created_by)
                or (request.profile in opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "message": "You do not have permission to create invoice from this opportunity",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Verify opportunity is CLOSED_WON
        if opportunity.stage != "CLOSED_WON":
            return Response(
                {
                    "error": True,
                    "message": "Invoice can only be created from CLOSED_WON opportunities",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify opportunity has line items
        line_items = opportunity.line_items.all()
        if not line_items.exists():
            return Response(
                {
                    "error": True,
                    "message": "Opportunity has no products/line items to invoice",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if opportunity has an account
        if not opportunity.account:
            return Response(
                {
                    "error": True,
                    "message": "Opportunity must have an account to create an invoice",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get primary contact (first contact or None)
        contacts = opportunity.contacts.all()
        primary_contact = contacts.first() if contacts.exists() else None

        if not primary_contact:
            return Response(
                {
                    "error": True,
                    "message": "Opportunity must have at least one contact to create an invoice",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Generate invoice number
            last_invoice = (
                Invoice.objects.filter(org=org).order_by("-created_at").first()
            )
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.replace("INV-", ""))
                    new_number = f"INV-{last_num + 1:06d}"
                except ValueError:
                    new_number = (
                        f"INV-{Invoice.objects.filter(org=org).count() + 1:06d}"
                    )
            else:
                new_number = "INV-000001"

            # Create invoice
            invoice = Invoice.objects.create(
                invoice_number=new_number,
                title=f"Invoice for {opportunity.name}",
                account=opportunity.account,
                contact=primary_contact,
                opportunity=opportunity,
                currency=opportunity.currency or org.default_currency or "USD",
                status="DRAFT",
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=30),
                created_by=request.profile.user,
                org=org,
            )

            # Copy opportunity assigned users to invoice
            if opportunity.assigned_to.exists():
                invoice.assigned_to.set(opportunity.assigned_to.all())

            # Copy line items from opportunity to invoice
            for opp_item in line_items:
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product=opp_item.product,
                    name=opp_item.name,
                    description=opp_item.description,
                    quantity=opp_item.quantity,
                    unit_price=opp_item.unit_price,
                    discount_type=opp_item.discount_type or "",
                    discount_value=opp_item.discount_value,
                    tax_rate=Decimal("0"),  # No tax at creation, user can add later
                    order=opp_item.order,
                    org=org,
                )

            # Recalculate invoice totals
            invoice.recalculate_totals()
            invoice.save()

            # Create invoice history entry
            create_invoice_history.delay(
                str(invoice.id),
                str(request.profile.id),
                "created",
                f"Invoice created from opportunity: {opportunity.name}",
            )

        # Return the created invoice
        return Response(
            {
                "error": False,
                "message": "Invoice created successfully from opportunity",
                "invoice": InvoiceSerializer(invoice).data,
            },
            status=status.HTTP_201_CREATED,
        )
