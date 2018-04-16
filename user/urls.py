from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import RedirectView
from user import views
from .views import UserLogin

app_name = 'user'

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='user:login', permanent=False)),
    url(r'^login/$', UserLogin.as_view(), name='login'),
    url(r'^logout/$', views.logout, name='logout'),

]
