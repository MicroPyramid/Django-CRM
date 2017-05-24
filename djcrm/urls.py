from django.conf.urls import url
from djcrm import views
from django.contrib.auth import views as auth_views
app_name = 'djcrm'

urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^auth/$', auth_views.login, name="auth"),
]
