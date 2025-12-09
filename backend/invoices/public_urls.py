"""
Public URLs for client portal.

These URLs do not require authentication and are accessed via public tokens.
Mount at /api/public/ in main urls.py
"""

from django.urls import path

from invoices import public_views

app_name = "public_invoices"

urlpatterns = [
    # Public Invoice
    path(
        "invoice/<str:token>/",
        public_views.PublicInvoiceView.as_view(),
        name="public_invoice",
    ),
    path(
        "invoice/<str:token>/pdf/",
        public_views.PublicInvoicePDFView.as_view(),
        name="public_invoice_pdf",
    ),
    # Public Estimate
    path(
        "estimate/<str:token>/",
        public_views.PublicEstimateView.as_view(),
        name="public_estimate",
    ),
    path(
        "estimate/<str:token>/pdf/",
        public_views.PublicEstimatePDFView.as_view(),
        name="public_estimate_pdf",
    ),
    path(
        "estimate/<str:token>/accept/",
        public_views.PublicEstimateAcceptView.as_view(),
        name="public_estimate_accept",
    ),
    path(
        "estimate/<str:token>/decline/",
        public_views.PublicEstimateDeclineView.as_view(),
        name="public_estimate_decline",
    ),
]
