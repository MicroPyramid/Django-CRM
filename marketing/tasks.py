import datetime
import hashlib
from mimetypes import MimeTypes

import pytz
import requests
from celery.task import task
from django.core.management import call_command
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template import Context, Template

from common.utils import convert_to_custom_timezone
from marketing.models import (BlockedDomain, BlockedEmail, Campaign,
                              CampaignCompleted, CampaignLog, Contact,
                              ContactEmailCampaign, ContactList,
                              DuplicateContacts, FailedContact)


@task
def campaign_sechedule(request):
    pass


@task
def campaign_open(request):
    pass


@task
def campaign_click(request):
    pass


@task
def upload_csv_file(data, invalid_data, user, contact_lists):
    for each in data:
        contact = Contact.objects.filter(email=each['email']).first()
        if not contact:
            contact = Contact.objects.create(
                email=each['email'], created_by_id=user,
                name=each['first name'])
            if each.get('company name', None):
                contact.company_name = each['company name']
            if each.get('last name', None):
                contact.last_name = each['last name']
            if each.get('city', None):
                contact.city = each['city']
            if each.get("state", None):
                contact.state = each['state']
            contact.save()
        else:
            if not DuplicateContacts.objects.filter(
                contacts=contact,
                contact_list=ContactList.objects.get(id=int(contact_lists[0]))).exists():
                DuplicateContacts.objects.create(
                    contacts=contact,
                    contact_list=ContactList.objects.get(id=int(contact_lists[0])))
        for contact_list in contact_lists:
            contact.contact_list.add(
                ContactList.objects.get(id=int(contact_list)))

    for each in invalid_data:
        contact = FailedContact.objects.filter(email=each['email']).first()
        if not contact:
            contact = FailedContact.objects.create(
                email=each['email'], created_by_id=user,
                name=each['first name'])
            if each.get('company name', None):
                contact.company_name = each['company name']
            if each.get('last name', None):
                contact.last_name = each['last name']
            if each.get('city', None):
                contact.city = each['city']
            if each.get("state", None):
                contact.state = each['state']
            contact.save()
        for contact_list in contact_lists:
            contact.contact_list.add(
                ContactList.objects.get(id=int(contact_list)))


def send_campaign_mail(subject, content, from_email, to_email, bcc, reply_to, attachments):
    msg = EmailMessage(
        subject,
        content,
        from_email,
        to_email,
        bcc,
        reply_to=reply_to,
    )
    for attachment in attachments:
        msg.attach(*attachment)
    msg.content_subtype = "html"
    res = msg.send()
    print(res)


def get_campaign_message_id(campaign):
    hash_ = hashlib.md5()
    hash_.update(
        str(str(campaign.id) + str(campaign.campaign.created_by.id)).encode('utf-8') +
        str(datetime.datetime.now()).encode('utf-8')
    )
    file_hash = hash_.hexdigest()
    return file_hash


@task
def run_campaign(campaign, domain='demo.django-crm.io', protocol='https'):
    blocked_domains = BlockedDomain.objects.values_list('domain', flat=True)
    blocked_emails = BlockedEmail.objects.values_list('email', flat=True)
    try:
        campaign = Campaign.objects.get(id=campaign)
        attachments = []
        if campaign.attachment:
            file_path = campaign.attachment.path
            file_name = file_path.split("/")[-1]
            content = open(file_path, 'rb').read()
            mime = MimeTypes()
            mime_type = mime.guess_type(file_path)
            attachments.append((file_name, content, mime_type[0]))
        subject = campaign.subject

        contacts = Contact.objects.filter(
            contact_list__in=[each_list for each_list in campaign.contact_lists.all()])
        default_html = campaign.html_processed
        for each_contact in contacts:
            html = default_html
            campaign_log = CampaignLog.objects.create(contact=each_contact,
                                                      campaign=campaign)
            if campaign.reply_to_email:
                reply_to_email = campaign.reply_to_email
            else:
                message_id = get_campaign_message_id(campaign_log)
                campaign_log.message_id = message_id
                campaign_log.save()
                domain_name = 'django-crm.com'
                if campaign.from_email is not None:
                    from_email = campaign.from_email
                else:
                    from_email = campaign.created_by.email
                reply_to_email = str(from_email) + ' <' + \
                    str(message_id + '@' + domain_name + '') + '>'
            if not (each_contact.is_bounced or each_contact.is_unsubscribed):
                if ((each_contact.email not in blocked_emails) and (each_contact.email.split('@')[-1] not in blocked_domains)):
                    # domain_url = settings.URL_FOR_LINKS
                    domain_url = protocol + '://' + domain
                    img_src_url = domain_url + reverse('marketing:campaign_open', kwargs={
                        'campaign_log_id': campaign_log.id, 'email_id': each_contact.id})
                    # images can only be accessed over https
                    link = '<img src={img_src_url} alt="company_logo" title="company_logo" height="1" width="1" />'.format(
                        img_src_url=img_src_url)
                    # link = '<img src="' + domain_url + '/m/cm/track-email/' + \
                    #     str(campaign_log.id) + '/contact/' + \
                    #     str(each_contact.id) + '/" height="1" width="1" alt="company_logo" + \
                    #     title="company_logo"/>'

                    unsubscribe_from_campaign_url = reverse(
                        'marketing:unsubscribe_from_campaign', kwargs={'contact_id': each_contact.id,
                                                                    'campaign_id': campaign.id})
                    unsubscribe_from_campaign_html = "<br><br/><a href={}>Unsubscribe</a>".format(
                        domain_url + unsubscribe_from_campaign_url)
                    names_dict = {'company_name': each_contact.company_name if each_contact.company_name else '',
                                'last_name': each_contact.last_name if each_contact.last_name else '',
                                'city': each_contact.city if each_contact.city else '',
                                'state': each_contact.state if each_contact.state else '',
                                'first_name': each_contact.name,
                                'email': each_contact.email, 'email_id': each_contact.id,
                                'name': each_contact.name + ' ' + each_contact.last_name if each_contact.last_name else '',
                                'unsubscribe_from_campaign_url': unsubscribe_from_campaign_url}

                    html = Template(html).render(Context(names_dict))
                    mail_html = html + link + unsubscribe_from_campaign_html
                    from_email = str(campaign.from_name) + "<" + \
                        str(campaign.from_email) + '>'
                    to_email = [each_contact.email]
                    send_campaign_mail(
                        subject, mail_html, from_email, to_email, [], [reply_to_email], attachments)
    except Exception as e:
        print(e)
        pass


@task
def run_all_campaigns():
    start_date = datetime.date.today()
    campaigns = Campaign.objects.filter(schedule_date_time__date=start_date)
    for each in campaigns:
        run_campaign(each.id)


@task
def list_all_bounces_unsubscribes():
    bounces = requests.get('https://api.sendgrid.com/api/bounces.get.json?api_user=' +
                           settings.EMAIL_HOST_USER + '&api_key=' + settings.EMAIL_HOST_PASSWORD)
    for each in bounces.json():
        if type(each) == dict:
            contact = Contact.objects.filter(email=each.get('email')).first()
            if contact:
                contact.is_bounced = True
                contact.save()

    bounces = requests.get('https://api.sendgrid.com/api/unsubscribes.get.json?api_user=' +
                           settings.EMAIL_HOST_USER + '&api_key=' + settings.EMAIL_HOST_PASSWORD)
    for each in bounces.json():
        if type(each) == dict:
            contact = Contact.objects.filter(email=each.get('email')).first()
            if contact:
                contact.is_unsubscribed = True
                contact.save()


@task
def send_scheduled_campaigns():
    from datetime import datetime
    campaigns = Campaign.objects.filter(schedule_date_time__isnull=False)
    for each in campaigns:
        completed = CampaignCompleted.objects.filter(
            is_completed=True).values_list('campaign_id', flat=True)

        if each.id not in completed:
            schedule_date_time = each.schedule_date_time

            sent_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            sent_time = datetime.strptime(sent_time, '%Y-%m-%d %H:%M')
            local_tz = pytz.timezone(settings.TIME_ZONE)
            sent_time = local_tz.localize(sent_time)
            sent_time = convert_to_custom_timezone(
                sent_time, each.timezone, to_utc=True)

            if (
                str(each.schedule_date_time.date()) == str(sent_time.date()) and
                str(schedule_date_time.hour) == str(sent_time.hour)
            ):
                run_campaign.delay(each.id)
                CampaignCompleted.objects.create(
                    campaign=each, is_completed=True)


@task
def delete_multiple_contacts_tasks(contact_list_id, bounced=True):
    """ this method is used to remove all contacts from a contact list based on bounced kwarg """
    contacts_list_obj = ContactList.objects.filter(id=contact_list_id).first()
    if contacts_list_obj:
        contacts_objs = contacts_list_obj.contacts.filter(is_bounced=bounced)
        if contacts_objs:
            for contact_obj in contacts_objs:
                if contact_obj.contact_list.count() > 1:
                    contact_obj.contact_list.remove(contacts_list_obj)
                else:
                    contact_obj.delete()


@task
def send_campaign_email_to_admin_contact(campaign, domain='demo.django-crm.io', protocol='https'):
    try:
        campaign = Campaign.objects.get(id=campaign)
        attachments = []
        if campaign.attachment:
            file_path = campaign.attachment.path
            file_name = file_path.split("/")[-1]
            content = open(file_path, 'rb').read()
            mime = MimeTypes()
            mime_type = mime.guess_type(file_path)
            attachments.append((file_name, content, mime_type[0]))
        subject = campaign.subject
        contacts = ContactEmailCampaign.objects.all()
        default_html = campaign.html_processed
        blocked_domains = BlockedDomain.objects.values_list('domain', flat=True)
        blocked_emails = BlockedEmail.objects.values_list('email', flat=True)
        for each_contact in contacts:
            if ((each_contact.email not in blocked_emails) and (each_contact.email.split('@')[-1] not in blocked_domains)):
                html = default_html
                if campaign.reply_to_email:
                    reply_to_email = campaign.reply_to_email
                else:
                    domain_name = 'django-crm.com'
                    if campaign.from_email is not None:
                        from_email = campaign.from_email
                    else:
                        from_email = campaign.created_by.email
                    reply_to_email = str(from_email) + ' <' + \
                        str(settings.EMAIL_HOST_USER + '@' + domain_name + '') + '>'

                # domain_url = settings.URL_FOR_LINKS
                domain_url = protocol + '://' + domain
                # img_src_url = domain_url + reverse('marketing:campaign_open', kwargs={
                #     'campaign_log_id': campaign_log.id, 'email_id': each_contact.id})
                # # images can only be accessed over https
                # link = '<img src={img_src_url} alt="company_logo" title="company_logo" height="1" width="1" />'.format(
                #     img_src_url=img_src_url)
                # link = '<img src="' + domain_url + '/m/cm/track-email/' + \
                #     str(campaign_log.id) + '/contact/' + \
                #     str(each_contact.id) + '/" height="1" width="1" alt="company_logo" + \
                #     title="company_logo"/>'

                # unsubscribe_from_campaign_url = reverse(
                #     'marketing:unsubscribe_from_campaign', kwargs={'contact_id': each_contact.id,
                #                                                     'campaign_id': campaign.id})
                # unsubscribe_from_campaign_html = "<br><br/><a href={}>Unsubscribe</a>".format(
                #     domain_url + unsubscribe_from_campaign_url)

                # names_dict = {'company_name': '', 'city': '', 'state': '',
                #                 'last_name': each_contact.last_name if each_contact.last_name else '',
                #                 'email': each_contact.email, 'email_id': each_contact.id,
                #                 'name': each_contact.name + ' ' + each_contact.last_name if each_contact.last_name else '',
                #             }

                # mail_html = html + link + unsubscribe_from_campaign_html
                html = Template(html).render(Context({'email_id': each_contact.id}))
                mail_html = html
                from_email = str(campaign.from_name) + "<" + \
                    str(campaign.from_email) + '>'
                to_email = [each_contact.email]
                send_campaign_mail(
                    subject, mail_html, from_email, to_email, [], [reply_to_email], attachments)
    except Exception as e:
        print(e)
        pass

@task
def update_elastic_search_index():
    call_command('update_index')