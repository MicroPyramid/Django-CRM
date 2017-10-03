from django.conf.urls import url
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'emails'


urlpatterns = [
    url(r'^list/', views.emails_list, name="list"),
    url(r'^compose/', views.email, name="compose"),
    url(r'^email_sent/', views.email_sent, name="email_sent"),
    url(r'^email_move_to_trash/(?P<pk>\d+)/$',
        views.email_move_to_trash, name='email_move_to_trash'),
    url(r'^email_delete/(?P<pk>\d+)/$',
        views.email_delete, name='email_delete'),
    url(r'^email_trash/', views.email_trash, name="email_trash"),
    url(r'^email_trash_delete/(?P<pk>\d+)/$',
        views.email_trash_delete, name="email_trash_delete"),
    url(r'^email_draft/', views.email_draft, name="email_draft"),
    url(r'^email_draft_delete/(?P<pk>\d+)/$',
        views.email_draft_delete, name="email_draft_delete"),
    url(r'^email_imp/(?P<pk>\d+)/$', views.email_imp, name="email_imp"),
    url(r'^email_imp_list/', views.email_imp_list, name="email_imp_list"),
    url(r'^email_sent_edit/(?P<pk>\d+)/$',
        views.email_sent_edit, name="email_sent_edit"),
    url(r'^email_unimp/(?P<pk>\d+)/$', views.email_unimp, name="email_unimp"),
    url(r'^email_view/(?P<pk>\d+)/$', views.email_view, name="email_view"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
