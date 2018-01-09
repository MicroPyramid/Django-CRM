from django.conf.urls import url
from opportunity import views

app_name = 'oppurtunity'


urlpatterns = [
    url(r'^list/$', views.opp_list, name='list'),
    url(r'^create/$', views.opp_create, name='save'),
    url(r'^(?P<pk>\d+)/view/$', views.opp_view, name='opp_view'),
    url(r'^(?P<pk>\d+)/edit/$', views.opp_edit, name='opp_edit'),
    url(r'^(?P<pk>\d+)/delete/$', views.opp_remove, name='opp_remove'),
    url(r'^contacts/$', views.contacts, name='contacts'),
    url(r'^get/list/$', views.get_opportunity, name='get_opportunity'),
    # comments
    url(r'^comment/add/$', views.add_comment, name='add_comment'),
    url(r'^comment/edit/$', views.edit_comment, name='edit_comment'),
    url(r'^comment/remove/$', views.remove_comment, name='remove_comment'),
]
