from django.urls import path

from cases.views import AddAttachmentView
from cases.views import AddCommentView
from cases.views import CaseDetailView
from cases.views import CasesListView
from cases.views import CloseCaseView
from cases.views import CreateCaseView
from cases.views import DeleteAttachmentsView
from cases.views import DeleteCommentView
from cases.views import GetCasesView
from cases.views import RemoveCaseView
from cases.views import SelectContactsView
from cases.views import UpdateCaseView
from cases.views import UpdateCommentView

app_name = 'cases'

urlpatterns = [
    path('list/', CasesListView.as_view(), name='list'),
    path('create/', CreateCaseView.as_view(), name='add_case'),
    path('<int:pk>/view/', CaseDetailView.as_view(), name='view_case'),
    path('<int:pk>/edit_case/', UpdateCaseView.as_view(), name='edit_case'),
    path('<int:case_id>/remove/', RemoveCaseView.as_view(), name='remove_case'),

    path('close_case/', CloseCaseView.as_view(), name='close_case'),
    path('select_contacts/', SelectContactsView.as_view(), name='select_contacts'),
    path('get/list/', GetCasesView.as_view(), name='get_cases'),

    path('comment/add/', AddCommentView.as_view(), name='add_comment'),
    path('comment/edit/', UpdateCommentView.as_view(), name='edit_comment'),
    path('comment/remove/', DeleteCommentView.as_view(), name='remove_comment'),

    path('attachment/add/', AddAttachmentView.as_view(), name='add_attachment'),
    path(
        'attachment/remove/', DeleteAttachmentsView.as_view(),
        name='remove_attachment',
    ),
]
