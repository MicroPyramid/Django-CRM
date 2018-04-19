from user import views
from django.conf.urls import url
#from django.contrib.auth import views as auth_views
#from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import RedirectView
from .views import UserView, UserDelete, UserEdit, UserLogin, UserCreate, UserUpdatePass, UserList

app_name = 'user'

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='user:login', permanent=False)),
    url(r'^login/$', UserLogin.as_view(), name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^create/$', UserCreate.as_view(), name='create'),
    url(r'^change-password/$', UserUpdatePass.as_view(), name="change_pass"),
    url(r'^list/$', UserList.as_view(), name="list"),
    # TODO these are not really implemented yet
    url(r'^(?P<user_id>\d*)/view/$', UserView.as_view(), name="view"),
    url(r'^(?P<user_id>\d*)/update/$', UserEdit.as_view(), name="update"),
    url(r'^(?P<user_id>\d*)/delete/$', UserDelete.as_view(), name="delete"),
]
