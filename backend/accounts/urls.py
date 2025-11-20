from django.urls import path

from accounts import views

app_name = "api_accounts"

urlpatterns = [
    path("", views.AccountsListView.as_view()),
    path("<str:pk>/", views.AccountDetailView.as_view()),
    path("<str:pk>/create_mail/", views.AccountCreateMailView.as_view()),
    path("comment/<str:pk>/", views.AccountCommentView.as_view()),
    path("attachment/<str:pk>/", views.AccountAttachmentView.as_view()),
]
