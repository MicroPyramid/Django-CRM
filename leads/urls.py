from django.urls import path

from leads.views import AddAttachmentsView
from leads.views import AddCommentView
from leads.views import ConvertLeadView
from leads.views import CreateLeadView
from leads.views import DeleteAttachmentsView
from leads.views import DeleteCommentView
from leads.views import DeleteLeadView
from leads.views import GetLeadsView
from leads.views import LeadDetailView
from leads.views import LeadListView
from leads.views import UpdateCommentView
from leads.views import UpdateLeadView


app_name = 'leads'


urlpatterns = [
    path('list/', LeadListView.as_view(), name='list'),
    path('create/', CreateLeadView.as_view(), name='add_lead'),
    path('<int:pk>/view/', LeadDetailView.as_view(), name='view_lead'),
    path('<int:pk>/edit/', UpdateLeadView.as_view(), name='edit_lead'),
    path('<int:pk>/delete/', DeleteLeadView.as_view(), name='remove_lead'),
    path('<int:pk>/convert/', ConvertLeadView.as_view(), name='leads_convert'),

    path('get/list/', GetLeadsView.as_view(), name='get_lead'),

    path('comment/add/', AddCommentView.as_view(), name='add_comment'),
    path('comment/edit/', UpdateCommentView.as_view(), name='edit_comment'),
    path('comment/remove/', DeleteCommentView.as_view(), name='remove_comment'),

    path('attachment/add/', AddAttachmentsView.as_view(), name='add_attachment'),
    path(
        'attachment/remove/', DeleteAttachmentsView.as_view(),
        name='remove_attachment',
    ),
]
