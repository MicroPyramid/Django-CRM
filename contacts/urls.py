from django.conf.urls import url
from .import views

app_name = 'contacts'


urlpatterns = [
    url(r'^list/$', views.display_contact, name='list'),
    url(r'^create/$', views.add_contact, name='add_contact'),
    url(r'^(?P<pk>\d+)/edit/$', views.edit_contact, name='edit_contact'),
    url(r'^(?P<pk>\d+)/delete/$', views.delete_contact, name='delete_contact'),
    url(r'^(?P<pk>\d+)/view/$', views.view_contact, name='view_contact'),
    url(r'^comment_create/$', views.comment_add, name='comment_add'),
    url(r'^comment_edit/$', views.comment_edit, name='comment_edit'),
    url(r'^comment_remove/$', views.comment_remove, name='comment_remove'),
    url(r'^get/list/$', views.get_contacts, name='get_contacts'),
]
