from django.urls import path
from leads.views import (
    LeadListView, create_lead, LeadDetailView,
    update_lead, DeleteLeadView, convert_lead,
    GetLeadsView, AddCommentView, UpdateCommentView, DeleteCommentView,
    AddAttachmentsView, DeleteAttachmentsView, create_lead_from_site,
    update_lead_tags, remove_lead_tag, upload_lead_csv_file, sample_lead_file,
    lead_list_view, get_teams_and_users
)


app_name = 'leads'


urlpatterns = [
#     path('', LeadListView.as_view(), name='list'),
    path('', lead_list_view, name='list'),
    path('create/', create_lead, name='add_lead'),
    # create_lead_from_site
    path('create/from-site/', create_lead_from_site,
         name="create_lead_from_site"),
    path('<int:pk>/view/', LeadDetailView.as_view(), name="view_lead"),
    path('<int:pk>/edit/', update_lead, name="edit_lead"),
    path('<int:pk>/delete/', DeleteLeadView.as_view(), name="remove_lead"),
    path('<int:pk>/convert/', convert_lead, name="leads_convert"),

    path('get/list/', GetLeadsView.as_view(), name="get_lead"),

    path('comment/add/', AddCommentView.as_view(), name="add_comment"),
    path('comment/edit/', UpdateCommentView.as_view(), name="edit_comment"),
    path('comment/remove/',
         DeleteCommentView.as_view(), name="remove_comment"),

    path('attachment/add/',
         AddAttachmentsView.as_view(), name="add_attachment"),
    path('attachment/remove/', DeleteAttachmentsView.as_view(),
         name="remove_attachment"),
    path('update_lead_tags/<pk>/', update_lead_tags, name="update_lead_tags"),
    path('remove_lead_tag/', remove_lead_tag, name="remove_lead_tag"),
    path('upload_lead_csv_file/', upload_lead_csv_file, name="upload_lead_csv_file"),
    path('sample_lead_file/', sample_lead_file, name="sample_lead_file"),
    path('get_teams_and_users/', get_teams_and_users, name="get_teams_and_users")
]
