from django.urls import path
from boards import views

app_name = "api_boards"

urlpatterns = [
    # Boards
    path("", views.BoardListCreateView.as_view(), name="board_list_create"),
    path("<str:pk>/", views.BoardDetailView.as_view(), name="board_detail"),

    # Columns
    path("<str:board_pk>/columns/", views.BoardColumnListCreateView.as_view(), name="column_list_create"),

    # Tasks
    path("columns/<str:column_pk>/tasks/", views.BoardTaskListCreateView.as_view(), name="task_list_create"),
    path("tasks/<str:pk>/", views.BoardTaskDetailView.as_view(), name="task_detail"),
]
