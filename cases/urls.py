from django.conf.urls import url
from cases import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'cases'


urlpatterns = [
    url(r'^list/$', views.cases, name='list'),
    url(r'^create/$', views.case_add, name='case_add'),
    url(r'^(?P<case_id>\d+)/view/$', views.show_case, name='show-case'),
    url(r'^editdetails/$', views.editdetails, name='editdetails'),
    url(r'^(?P<case_id>\d+)/edit_case/$', views.edit_case, name='edit_case'),
    url(r'^close_case/$', views.close_case, name="close_case"),
    url(r'^(?P<case_id>\d+)/delete/$', views.remove_case, name='delete_case'),
    url(r'^select_contacts/$', views.selectContacts, name="select_contacts"),
    url(r'^edit_comment/$', views.comment_edit, name='edit_comment'),
    url(r'^create_comment/$', views.comment_add, name='create_comment'),
    url(r'^remove_comment/$', views.comment_remove, name='remove_comment'),
    url(r'^remove_comment_file/$', views.remove_commentfile, name='remove_commentfile'),
    url(r'^(?P<com_id>\d+)/download/$', views.down_file, name='download_comfile'),
    url(r'^get/list/$', views.get_cases, name='get_cases'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
