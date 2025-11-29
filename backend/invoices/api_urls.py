from django.urls import path

from invoices import api_views

app_name = "api_invoices"

urlpatterns = [
    path("", api_views.InvoiceListView.as_view()),
    path("<str:pk>/", api_views.InvoiceDetailView.as_view()),
    path("comment/<str:pk>/", api_views.InvoiceCommentView.as_view()),
    path("attachment/<str:pk>/", api_views.InvoiceAttachmentView.as_view()),
]
