from django.urls import path

from accounts import views

app_name = "api_accounts"

urlpatterns = [
    path("", views.AccountsListView.as_view()),
    path("<int:pk>/", views.AccountDetailView.as_view()),
    path("<int:pk>/create_mail/", views.AccountCreateMailView.as_view()),
    path("comment/<int:pk>/", views.AccountCommentView.as_view()),
    path("attachment/<int:pk>/", views.AccountAttachmentView.as_view()),
]
