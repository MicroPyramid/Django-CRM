from django.conf.urls import url
from accounts import views

app_name = 'accounts'


urlpatterns = [
    url(r'^list/$', views.accounts_list, name='list'),
    url(r'^create/$', views.add_account, name='new_account'),
    url(r'^(?P<account_id>\d*)/view/$', views.view_account, name="view_account"),
    url(r'^(?P<edid>\d*)/edit/$', views.edit_account, name="edit_account"),
    url(r'^(?P<aid>\d*)/delete/$', views.remove_account, name="remove_account"),

    url(r'^comment/add/$', views.add_comment, name='add_comment'),
    url(r'^comment/edit/$', views.edit_comment, name='edit_comment'),
    url(r'^comment/remove/$', views.remove_comment, name='remove_comment'),
]
