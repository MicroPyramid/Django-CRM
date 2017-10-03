from django.conf.urls import url
from leads import views

app_name = 'leads'


urlpatterns = [


    url(r'^list/$', views.display, name='list'),
    url(r'^create/$', views.add_lead, name='add_lead'),
    url(r'^(?P<pk>\d+)/edit/$', views.edit_lead, name='edit_lead'),
    url(r'^(?P<pk>\d+)/delete/$', views.delete_lead, name="delete_lead"),
    url(r'^(?P<pk>\d+)/view/$', views.view_lead, name="view_lead"),
    url(r'^create_comment/$', views.comment_add, name='create_comment'),
    url(r'^remove_comment/$', views.comment_remove, name='remove_comment'),
    url(r'^get/list/$', views.get_leads, name='get_lead'),
    url(r'^(?P<pk>\d+)/convert/$', views.leads_convert, name='leads_convert'),
]
