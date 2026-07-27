"""
Centralised object-level authorization for invoice-scoped endpoints.

Every invoice endpoint must answer the same two questions in the same order:

1. Does this invoice exist *in the caller's org*?  -> 404 if not, so that a
   caller in another org cannot probe for invoice IDs.
2. May this caller act on it?                      -> 403 if not.

Before this module each view hand-rolled that logic, and several views
(``send``, ``mark-paid``, ``duplicate``, line items, payments, comments,
attachments) skipped step 2 entirely -- see GitHub issue #698. Route every new
invoice endpoint through :func:`get_invoice_or_error` rather than re-deriving
the rule.
"""

from rest_framework import status
from rest_framework.response import Response

from invoices.models import Invoice

INVOICE_NOT_FOUND = "Invoice not found"
PERMISSION_DENIED = "Permission denied"


def has_invoice_object_access(request, invoice):
    """Return True if the caller may read and act on ``invoice``.

    Access is granted to org admins, Django superusers, the user who created
    the invoice, and any profile it is assigned to.

    Note ``created_by`` is a ``User`` FK (from ``UserAuditModel``) while
    ``assigned_to`` holds ``Profile`` rows, so the two checks compare against
    different objects. Comparing ``request.profile`` to ``created_by`` -- as
    the pre-existing copies of this check did -- is always False and silently
    locks creators out of their own invoices.
    """
    profile = request.profile

    if profile.role == "ADMIN" or request.user.is_superuser:
        return True

    if invoice.created_by_id and invoice.created_by_id == request.user.id:
        return True

    return invoice.assigned_to.filter(id=profile.id).exists()


def get_invoice_or_error(request, invoice_id, queryset=None):
    """Fetch an org-scoped invoice and authorize the caller against it.

    Returns ``(invoice, None)`` on success, or ``(None, response)`` holding the
    404/403 the view should return. Callers must check the error first::

        invoice, error = get_invoice_or_error(request, pk)
        if error:
            return error
    """
    qs = Invoice.objects.all() if queryset is None else queryset
    invoice = qs.filter(id=invoice_id, org=request.profile.org).first()

    if not invoice:
        return None, Response(
            {"error": True, "message": INVOICE_NOT_FOUND},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not has_invoice_object_access(request, invoice):
        return None, Response(
            {"error": True, "message": PERMISSION_DENIED},
            status=status.HTTP_403_FORBIDDEN,
        )

    return invoice, None
