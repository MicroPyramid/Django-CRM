from django.urls import path
from cases.views import (
    CasesListView, create_case, CaseDetailView, update_case, RemoveCaseView,
    CloseCaseView, select_contact, GetCasesView, AddCommentView,
    UpdateCommentView, DeleteCommentView,
    AddAttachmentView, DeleteAttachmentsView)

app_name = 'cases'

urlpatterns = [
    path('', CasesListView.as_view(), name='list'),
    path('create/', create_case, name='add_case'),
    path('<int:pk>/view/', CaseDetailView.as_view(), name="view_case"),
    path('<int:pk>/edit_case/', update_case, name="edit_case"),
    path('<int:case_id>/remove/',
         RemoveCaseView.as_view(), name="remove_case"),

    path('close_case/', CloseCaseView.as_view(), name="close_case"),
    path('select_contacts/', select_contact, name="select_contacts"),
    path('get/list/', GetCasesView.as_view(), name="get_cases"),

    path('comment/add/', AddCommentView.as_view(), name="add_comment"),
    path('comment/edit/', UpdateCommentView.as_view(), name="edit_comment"),
    path('comment/remove/',
         DeleteCommentView.as_view(), name="remove_comment"),

    path('attachment/add/',
         AddAttachmentView.as_view(), name="add_attachment"),
    path('attachment/remove/', DeleteAttachmentsView.as_view(),
         name="remove_attachment"),
]
