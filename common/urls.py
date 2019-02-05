from django.contrib.auth import views as auth_views

from django.urls import path, re_path
from common.views import (
    HomeView, LoginView, ForgotPasswordView, LogoutView, ChangePasswordView, ProfileView,
    UsersListView, CreateUserView, UpdateUserView, UserDetailView, UserDeleteView, PasswordResetView,
    DocumentListView, DocumentCreateView, UpdateDocumentView, DocumentDetailView, DocumentDeleteView, 
    download_document, change_user_status, download_attachment)
from django.conf.urls.static import static
from django.conf import settings


app_name = 'common'


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/', ProfileView.as_view(), name='profile'),

    # User views
    path('users/list/', UsersListView.as_view(), name='users_list'),
    path('users/create/', CreateUserView.as_view(), name='create_user'),
    path('users/<int:pk>/edit/', UpdateUserView.as_view(), name="edit_user"),
    path('users/<int:pk>/view/', UserDetailView.as_view(), name='view_user'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='remove_user'),

    path(
        'password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path(
        'reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Document
    path('documents/list/', DocumentListView.as_view(), name='doc_list'),
    path('documents/create/', DocumentCreateView.as_view(), name='create_doc'),
    path('documents/<int:pk>/edit/', UpdateDocumentView.as_view(), name="edit_doc"),
    path('documents/<int:pk>/view/', DocumentDetailView.as_view(), name='view_doc'),
    path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='remove_doc'),

    # download
    path('documents/<int:pk>/download/', download_document, name='download_document'),

    # download_attachment
     path('attachments/<int:pk>/download/', download_attachment, name='download_attachment'),

    path('user/status/<int:pk>/', change_user_status, name='change_user_status'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
