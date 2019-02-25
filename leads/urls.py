from django.urls import path
from leads.views import (
    LeadListView, CreateLeadView, LeadDetailView, UpdateLeadView, DeleteLeadView, ConvertLeadView,
    GetLeadsView, AddCommentView, UpdateCommentView, DeleteCommentView,
    AddAttachmentsView, DeleteAttachmentsView, create_lead_from_site
)


app_name = 'leads'


urlpatterns = [
    path('list/', LeadListView.as_view(), name='list'),
    path('create/', CreateLeadView.as_view(), name='add_lead'),
    # create_lead_from_site
    path('create/from-site/', create_lead_from_site,
         name="create_lead_from_site"),
    path('<int:pk>/view/', LeadDetailView.as_view(), name="view_lead"),
    path('<int:pk>/edit/', UpdateLeadView.as_view(), name="edit_lead"),
    path('<int:pk>/delete/', DeleteLeadView.as_view(), name="remove_lead"),
    path('<int:pk>/convert/', ConvertLeadView.as_view(), name="leads_convert"),

    path('get/list/', GetLeadsView.as_view(), name="get_lead"),

    path('comment/add/', AddCommentView.as_view(), name="add_comment"),
    path('comment/edit/', UpdateCommentView.as_view(), name="edit_comment"),
    path('comment/remove/', DeleteCommentView.as_view(), name="remove_comment"),

    path('attachment/add/', AddAttachmentsView.as_view(), name="add_attachment"),
    path('attachment/remove/', DeleteAttachmentsView.as_view(),
         name="remove_attachment"),
]
