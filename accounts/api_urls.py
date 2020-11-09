from django.urls import path
from accounts import api_views

app_name = 'api_accounts'

urlpatterns = [
    path("accounts-list/", api_views.AccountsListView.as_view()),
    path("accounts-create/", api_views.CreateAccountView.as_view()),
    path("<int:pk>/view/", api_views.AccountDetailView.as_view()),
    path("accounts/<int:pk>/update/", api_views.AccountUpdateView.as_view()),
    path("accounts/<int:pk>/delete/", api_views.AccountDeleteView.as_view()),
]
