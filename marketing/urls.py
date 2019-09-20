from django.urls import path, include
from .views import (
    dashboard, contact_lists, contacts_list, contact_list_new, contact_list_detail, edit_contact,
    email_template_list, email_template_new, email_template_edit, email_template_delete,
    email_template_detail, campaign_list, campaign_new, campaign_details, campaign_delete,
    edit_contact_list, failed_contact_list_download_delete,
    campaign_link_click, campaign_open, demo_file_download, delete_contact, unsubscribe_from_campaign, contact_detail,
    download_contacts_for_campaign, create_campaign_from_template,
    download_links_clicked, delete_multiple_contacts, download_failed_contacts, delete_all_contacts,
    add_email_for_campaigns, list_all_emails_for_campaigns, edit_email_for_campaigns, delete_email_for_campaigns,
    add_blocked_domain, blocked_domain_list, edit_blocked_domain, delete_blocked_domain,
    add_blocked_email, blocked_email_list, edit_blocked_email, delete_blocked_email,
    contacts_list_elastic_search,
    # MarketingContactEmailSearch,
    # contacts_list_new
    # delete_contact_list
    # campaign_edit
    # edit_failed_contact
    # delete_failed_contact
    # failed_contact_list_detail
)

app_name = 'marketing'

urlpatterns = [
    path('', dashboard, name='dashboard'),

    path('contact-list/', contact_lists, name='contact_lists'),
    path('contacts/<int:pk>/edit/', edit_contact, name='edit_contact'),
    path('contacts/<int:pk>/delete/', delete_contact, name='delete_contact'),
    path('contacts/', contacts_list_elastic_search, name='contacts_list'),
    path('contact-list/create/', contact_list_new, name='contact_list_new'),
    # path('cl/list/cnew/', contacts_list_new, name='contacts_list_new'),
    path('contact-list/<int:pk>/detail/', contact_list_detail, name='contact_list_detail'),
    # path('contact-list/<int:pk>/failed/', failed_contact_list_detail, name='failed_contact_list_detail'),
    # path('contact-list/<int:pk>/failed/edit/', edit_failed_contact, name='edit_failed_contact'),
    # path('contact-list/<int:pk>/failed/delete/', delete_failed_contact, name='delete_failed_contact'),
    path('contact-list/<int:pk>/failed/download/',
         failed_contact_list_download_delete, name='failed_contact_list_download_delete'),
    path('contact-list/<int:pk>/edit/', edit_contact_list, name='edit_contact_list'),
    # path('cl/list/<int:pk>/delete/', delete_contact_list, name='delete_contact_list'),

    path('email-templates/', email_template_list, name='email_template_list'),
    path('email-templates/create/', email_template_new, name='email_template_new'),
    path('email-templates/<int:pk>/edit/', email_template_edit, name='email_template_edit'),
    path('email-templates/<int:pk>/detail/', email_template_detail, name='email_template_detail'),
    path('email-templates/<int:pk>/delete/', email_template_delete, name='email_template_delete'),

    path('campaigns/', campaign_list, name='campaign_list'),
    path('campaigns/create/', campaign_new, name='campaign_new'),
    # path('cm/<int:pk>/edit/', campaign_edit, name='campaign_edit'),
    path('campaigns/<int:pk>/details/', campaign_details, name='campaign_details'),
    path('campaigns/<int:pk>/delete/', campaign_delete, name='campaign_delete'),
    path('cm/link/<int:link_id>/e/<int:email_id>/', campaign_link_click, name='campaign_link_click'),
    path('cm/track-email/<int:campaign_log_id>/contact/<int:email_id>/', campaign_open, name='campaign_open'),
    path('demo-file-download-for-contacts-list/', demo_file_download, name='demo_file_download'),
    path('unsubscribe-from-campaign/<int:contact_id>/<int:campaign_id>/', unsubscribe_from_campaign, name="unsubscribe_from_campaign"),
    path('contacts/<int:contact_id>/view/', contact_detail, name="contact_detail"),
    path('download-contacts-for-campaign/<int:compaign_id>/', download_contacts_for_campaign, name="download_contacts_for_campaign"),
    path('create-campaign-from-template/<int:template_id>/', create_campaign_from_template, name="create_campaign_from_template"),
    path('download-links-clicked/<int:campaign_id>/', download_links_clicked, name="download_links_clicked"),
    path('delete_multiple_contacts/', delete_multiple_contacts, name="delete_multiple_contacts"),
    path('download-failed-contacts/<int:contact_list_id>/', download_failed_contacts, name="download_failed_contacts"),
    path('delete_all_contacts/<int:contact_list_id>/', delete_all_contacts, name="delete_all_contacts"),
    path('add-email-for-campaigns/', add_email_for_campaigns, name="add_email_for_campaigns"),
    path('list-all-emails-for-campaigns/', list_all_emails_for_campaigns, name="list_all_emails_for_campaigns"),
    path('edit-email-for-campaigns/<int:pk>/', edit_email_for_campaigns, name="edit_email_for_campaigns"),
    path('delete-email-for-campaigns/<int:pk>/', delete_email_for_campaigns, name="delete_email_for_campaigns"),

    path('add-blocked-domain/', add_blocked_domain, name="add_blocked_domain"),
    path('blocked-domain-list/', blocked_domain_list, name="blocked_domain_list"),
    path('edit-blocked-domain/<int:blocked_domain_id>/', edit_blocked_domain, name="edit_blocked_domain"),
    path('delete-blocked-domain/<int:blocked_domain_id>/', delete_blocked_domain, name="delete_blocked_domain"),

    path('add-blocked-email/', add_blocked_email, name="add_blocked_email"),
    path('blocked-email-list/', blocked_email_list, name="blocked_email_list"),
    path('edit-blocked-email/<int:blocked_email_id>/', edit_blocked_email, name="edit_blocked_email"),
    path('delete-blocked-email/<int:blocked_email_id>/', delete_blocked_email, name="delete_blocked_email"),

    path('search-marketing-contact-emails/', include('haystack.urls')),
    # path('elastic-search/', contacts_list_elastic_search),
]
