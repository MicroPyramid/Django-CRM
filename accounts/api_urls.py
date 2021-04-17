from django.urls import path
from accounts import api_views

app_name = "api_accounts"

urlpatterns = [
    path("", api_views.AccountsListView.as_view()),
    path("<int:pk>/", api_views.AccountDetailView.as_view()),
    path("<int:pk>/create_mail", api_views.AccountCreateMailView.as_view()),
    path("comment/<int:pk>/", api_views.AccountCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.AccountAttachmentView.as_view()),
]
