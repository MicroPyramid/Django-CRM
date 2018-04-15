from django.conf.urls import url
from common import views
from user import views as usr
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
app_name = 'common'


urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^login/$', RedirectView.as_view(pattern_name='user:login', permanent=False), name="login"),
    url(r'^logout/$', RedirectView.as_view(pattern_name='user:logout', permanent=False), name="logout"),
    url(r'^change-password/$', views.change_pass, name="change_pass"),
    url(r'^profile/$', views.profile, name="profile"),
    url(r'^users/list$', views.users_list, name="users_list"),
    url(r'^users/create$', views.create_user, name="create_user"),
    url(r'^user/(?P<user_id>\d*)/view/$', views.view_user, name="view_user"),
    url(r'^user/(?P<user_id>\d*)/edit/$', views.edit_user, name="edit_user"),
    url(r'^user/(?P<user_id>\d*)/delete/$', views.remove_user, name="remove_user"),
]
