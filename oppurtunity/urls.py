from django.conf.urls import url
from oppurtunity import views

app_name = 'oppurtunity'


urlpatterns = [

    url(r'^create/$', views.opp_create, name='save'),
    url(r'^list/$', views.opp_display, name='list'),
    url(r'^contacts/$', views.contacts, name='contacts'),
    url(r'^editdetails/$', views.editdetails, name='editdetails'),
    url(r'^comment_add/$', views.comment_add, name='comment_add'),
    url(r'^comment_edit/$', views.comment_edit, name='comment_edit'),
    url(r'^comment_remove/$', views.comment_remove, name='comment_remove'),
    url(r'^(?P<opp_id>\d+)/delete/$', views.opp_delete, name='opp_delete'),
    url(r'^(?P<opp_id>\d+)/edit/$', views.opp_edit, name='opp_edit'),
    url(r'^(?P<opp_id>\d+)/view/$', views.opp_view, name='opp_view'),
    # url(r'^get/list/$', views.get_opportunity, name='get_opportunity'),
]
