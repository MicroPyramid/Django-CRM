from django.conf.urls import url
from common import views
from django.contrib.auth import views as auth_views

from django.urls import path
from common.views import (
    HomeView, LoginView, ForgotPasswordView, LogoutView, ChangePasswordView, ProfileView,
    UsersListView, CreateUserView, UpdateUserView, UserDetailView, UserDeleteView)


app_name = 'common'


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_pass'),
    path('profile/', ProfileView.as_view(), name='profile'),

    # User views
    path('users/list/', UsersListView.as_view(), name='users_list'),
    path('users/create/', CreateUserView.as_view(), name='create_user'),
    path('users/<int:pk>/edit/', UpdateUserView.as_view(), name="edit_user"),
    path('users/<int:pk>/view/', UserDetailView.as_view(), name='view_user'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='remove_user'),

    url(r'^password_reset/$',auth_views.password_reset,name='password_reset'),
    url(r'^passowrd-reset/done/$',auth_views.password_reset_done,name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
     url(r'^reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),
]
