from django.conf.urls import url
from contacts import views

app_name = 'contacts'


urlpatterns = [
    url(r'^list/$', views.contacts_list, name='list'),
    url(r'^create/$', views.add_contact, name='add_contact'),
    url(r'^(?P<contact_id>\d+)/view/$', views.view_contact, name='view_contact'),
    url(r'^(?P<pk>\d+)/edit/$', views.edit_contact, name='edit_contact'),
    url(r'^(?P<pk>\d+)/delete/$', views.remove_contact, name='remove_contact'),
    url(r'^get/list/$', views.get_contacts, name='get_contacts'),
    # comments
    url(r'^comment/add/$', views.add_comment, name='add_comment'),
    url(r'^comment/edit/$', views.edit_comment, name='edit_comment'),
    url(r'^comment/remove/$', views.remove_comment, name='remove_comment'),
]
