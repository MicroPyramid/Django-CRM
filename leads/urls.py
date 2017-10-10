from django.conf.urls import url
from leads import views

app_name = 'leads'


urlpatterns = [
    url(r'^list/$', views.leads_list, name='list'),
    url(r'^create/$', views.add_lead, name='add_lead'),
    url(r'^(?P<lead_id>\d+)/view/$', views.view_lead, name="view_lead"),
    url(r'^(?P<lead_id>\d+)/edit/$', views.edit_lead, name='edit_lead'),
    url(r'^(?P<lead_id>\d+)/delete/$', views.remove_lead, name="remove_lead"),
    url(r'^(?P<pk>\d+)/convert/$', views.leads_convert, name='leads_convert'),
    # comments
    url(r'^comment/add/$', views.add_comment, name='add_comment'),
    url(r'^comment/edit/$', views.edit_comment, name='edit_comment'),
    url(r'^comment/remove/$', views.remove_comment, name='remove_comment'),
    url(r'^get/list/$', views.get_leads, name='get_lead'),
]
