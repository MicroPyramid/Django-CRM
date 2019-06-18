from django.urls import path
from invoices.views import *

app_name = 'invoices'


urlpatterns = [
    path('', invoices_list, name='invoices_list'),
    path('create/', invoices_create, name='invoices_create'),
    path('detail/<int:invoice_id>/', invoice_details, name='invoice_details'),
    path('edit/<int:invoice_id>/', invoice_edit, name='invoice_edit'),
    path('delete/<int:invoice_id>/', invoice_delete, name='invoice_delete'),
    path('download/<int:invoice_id>/', invoice_download, name='invoice_download'),
    path('send-mail/<int:invoice_id>/', invoice_send_mail, name='invoice_send_mail'),
    path('cancelled-mail/<int:invoice_id>/', invoice_change_status_cancelled, name='invoice_change_status_cancelled'),
    path('paid-mail/<int:invoice_id>/', invoice_change_status_paid, name='invoice_change_status_paid'),

    path('comment/add/', AddCommentView.as_view(), name="add_comment"),
    path('comment/edit/', UpdateCommentView.as_view(), name="edit_comment"),
    path('comment/remove/', DeleteCommentView.as_view(), name="remove_comment"),

    path('attachment/add/', AddAttachmentView.as_view(), name="add_attachment"),
    path('attachment/remove/', DeleteAttachmentsView.as_view(),
         name="remove_attachment"),

]
