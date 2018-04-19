from django.conf.urls import url
from common import views

from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
app_name = 'common'


urlpatterns = [
    url(r'^$',  RedirectView.as_view(pattern_name='user:list'), name="home"),
]
