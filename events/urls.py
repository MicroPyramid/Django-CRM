from django.urls import path
from events.views import *

app_name = 'events'


urlpatterns = [
    path('', events_list, name='events_list'),
    path('create/', event_create, name='event_create'),
    path('detail/<int:event_id>/', event_detail_view, name='detail_view'),
    path('edit/<int:event_id>/', event_update, name='event_update'),
    path('delete/<int:event_id>/', event_delete, name='event_delete'),

    path('comment/add/', AddCommentView.as_view(), name="add_comment"),
    path('comment/edit/', UpdateCommentView.as_view(), name="edit_comment"),
    path('comment/remove/', DeleteCommentView.as_view(), name="remove_comment"),

    path('attachment/add/', AddAttachmentView.as_view(), name="add_attachment"),
    path('attachment/remove/', DeleteAttachmentsView.as_view(),
         name="remove_attachment"),
]
