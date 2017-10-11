from django.conf.urls import url
from cases import views

app_name = 'cases'


urlpatterns = [
    url(r'^list/$', views.cases_list, name='list'),
    url(r'^create/$', views.add_case, name='add_case'),
    url(r'^(?P<case_id>\d+)/view/$', views.view_case, name='view_case'),
    url(r'^(?P<case_id>\d+)/edit_case/$', views.edit_case, name='edit_case'),
    url(r'^close_case/$', views.close_case, name="close_case"),
    url(r'^(?P<case_id>\d+)/remove/$', views.remove_case, name='remove_case'),
    url(r'^select_contacts/$', views.selectContacts, name="select_contacts"),
    url(r'^get/list/$', views.get_cases, name='get_cases'),
    # comments
    url(r'^comment/add/$', views.add_comment, name='add_comment'),
    url(r'^comment/edit/$', views.edit_comment, name='edit_comment'),
    url(r'^comment/remove/$', views.remove_comment, name='remove_comment'),
]
