from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import RedirectView

app_name = 'user'

urlpatterns = [
    url(r'^login/$', auth_views.login, {'template_name': 'user/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'user/logged_out.html'}, name='logout'),
]
