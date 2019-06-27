from django.urls import path
from tasks.views import *

app_name = 'tasks'


urlpatterns = [
    path('', tasks_list, name='tasks_list'),
    path('create/', task_create, name='task_create'),
    path('detail/<int:task_id>/', task_detail, name='task_detail'),
    path('edit/<int:task_id>/', task_edit, name='task_edit'),
    path('delete/<int:task_id>/', task_delete, name='task_delete'),

    path('comment/add/', AddCommentView.as_view(), name="add_comment"),
    path('comment/edit/', UpdateCommentView.as_view(), name="edit_comment"),
    path('comment/remove/', DeleteCommentView.as_view(), name="remove_comment"),

    path('attachment/add/', AddAttachmentView.as_view(), name="add_attachment"),
    path('attachment/remove/', DeleteAttachmentsView.as_view(),
         name="remove_attachment"),
]
