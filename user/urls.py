from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import RedirectView
from user import views
from .views import UserLogin, UserCreate, UserUpdatePass

app_name = 'user'

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='user:login', permanent=False)),
    url(r'^login/$', UserLogin.as_view(), name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^create/$', UserCreate.as_view(), name='create'),
    url(r'^change-password/$', UserUpdatePass.as_view(), name="change_pass"),
]
