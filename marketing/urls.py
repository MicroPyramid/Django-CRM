from django.urls import path
from .views import (
    dashboard, contact_lists, contacts_list, contact_list_new, contacts_list_new, contact_list_detail, edit_contact,
    email_template_list, email_template_new, email_template_edit,
    email_template_detail, campaign_list, campaign_new, campaign_edit, campaign_details
)

app_name = 'marketing'

urlpatterns = [
    path('', dashboard, name='dashboard'),

    path('cl/all/', contact_lists, name='contact_lists'),
    path('cl/edit_contact/', edit_contact, name='edit_contact'),
    path('cl/lists/', contacts_list, name='contacts_list'),
    path('cl/list/new/', contact_list_new, name='contact_list_new'),
    path('cl/list/cnew/', contacts_list_new, name='contacts_list_new'),
    path('cl/list/detail/', contact_list_detail, name='contact_list_detail'),

    path('et/list/', email_template_list, name='email_template_list'),
    path('et/new/', email_template_new, name='email_template_new'),
    path('et/edit/', email_template_edit, name='email_template_edit'),
    path('et/detail/', email_template_detail, name='email_template_detail'),

    path('cm/list/', campaign_list, name='campaign_list'),
    path('cm/new/', campaign_new, name='campaign_new'),
    path('cm/edit/', campaign_edit, name='campaign_edit'),
    path('cm/details/', campaign_details, name='campaign_details')
]
