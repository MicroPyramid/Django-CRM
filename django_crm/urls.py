from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views, forms


urlpatterns = [

    url(r'^', include('django_crm.djcrm.urls', namespace='djcrm_app')),
    url(r'^accounts/', include('django_crm.accounts.urls', namespace='accounts')),
    url(r'^leads/', include('django_crm.leads.urls', namespace='leads')),
    url(r'^contacts/', include('django_crm.contacts.urls', namespace='contacts')),
    url(r'^oppurtunities/', include('django_crm.oppurtunity.urls', namespace='oppurtunities')),
    url(r'^cases/', include('django_crm.cases.urls', namespace='cases')),
    url(r'^emails/', include('django_crm.emails.urls', namespace='emails')),
    url(r'^planner/', include('django_crm.planner.urls', namespace='planner')),
    url(r'^login/$', views.login, {'template_name': 'login.html', 'authentication_form': forms.AuthenticationForm}, name='login'),
    url(r'^logout/$', views.logout, {'next_page': '/login/'}, name='logout'),

]
