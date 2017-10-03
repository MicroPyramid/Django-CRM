from django.conf.urls import url
from accounts import views

app_name = 'accounts'


urlpatterns = [
    url(r'^list/$', views.account, name='list'),
    url(r'^create/$', views.new_account, name='new_account'),
    url(r'^(?P<aid>\d*)/view/$', views.view_account, name="view_account"),
    url(r'^(?P<edid>\d*)/edit/$', views.edit_account, name="edit_account"),
    url(r'^(?P<aid>\d*)/delete/$', views.remove_account, name="remove_account"),
    url(r'^comment/add/$', views.comment_add, name='comment_add'),
    url(r'^comment/remove/$', views.comment_remove, name='comment_remove'),
    url(r'^comment/edit/$', views.comment_edit, name='comment_edit'),
    url(r'^get/list/$', views.get_accounts, name='get_accounts'),
]
