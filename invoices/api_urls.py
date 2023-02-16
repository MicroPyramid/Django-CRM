from django.urls import path

from invoices import api_views

app_name = "api_invoices"

urlpatterns = [
    path("", api_views.InvoiceListView.as_view()),
    path("<int:pk>/", api_views.InvoiceDetailView.as_view()),
    path("comment/<int:pk>/", api_views.InvoiceCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.InvoiceAttachmentView.as_view()),
]
