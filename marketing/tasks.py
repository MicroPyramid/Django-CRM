import datetime
import hashlib
import pytz
import requests
from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Template, Context
from common.utils import convert_to_custom_timezone
from marketing.models import Contact, ContactList, Campaign, CampaignLog


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
def upload_csv_file(data, user, contact_lists):
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
        for contact_list in contact_lists:
            contact.contact_list.add(ContactList.objects.get(id=int(contact_list)))


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
    print (res)


def get_campaign_message_id(campaign):
    hash_ = hashlib.md5()
    hash_.update(
        str(str(campaign.id) + str(campaign.campaign.created_by.id)).encode('utf-8') +
        str(datetime.datetime.now()).encode('utf-8')
    )
    file_hash = hash_.hexdigest()
    return file_hash


@task
def run_campaign(campaign):
    try:
        campaign = Campaign.objects.get(id=campaign)
        subject = campaign.subject
        # project_settings = Settings.objects.filter().first()

        contacts = []
        for each_list in campaign.contact_lists.all():
            contacts = Contact.objects.filter(contact_list__in=[each_list])
        # contacts = campaign.contacts.filter(Q(is_bounced=False) | Q(is_unsubscribed=False)).distinct()
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
                domain_name = settings.SUBDOMAIN_NAME + '.' + project_settings.domain if project_settings else ''
                # domain_name = 'micro.peeljobs.com'
                if campaign.from_email is not None:
                    from_email = campaign.from_email
                else:
                    from_email = campaign.created_by.email
                reply_to_email = str(from_email) + ' <' + str(message_id + '@' + domain_name + '') + '>'
            if not (each_contact.is_bounced or each_contact.is_unsubscribed):
                # link = '<img src="https://micropyramid.localtunnel.me/track-email/' + \
                #     str(campaign_log.id) + '/" height="1" width="1"</img>'
                domain_url = '%s%s' % (settings.SCHEME, settings.HOST_URL)
                link = '<img src="' + domain_url + '/track-email/' + \
                    str(campaign_log.id) + '/contact/' + str(each_contact.id) + '/" height="1" width="1" />'
                names_dict = {'company_name': each_contact.company_name if each_contact.company_name else '',
                              'last_name': each_contact.last_name if each_contact.last_name else '',
                              'city': each_contact.city if each_contact.city else '',
                              'state': each_contact.state if each_contact.state else '',
                              'first_name': each_contact.name,
                              'email': each_contact.email, 'email_id': each_contact.id}

                html = Template(html).render(Context(names_dict))
                mail_html = html + link
                from_email = str(campaign.from_name) + "<" + str(campaign.from_email) + '>'
                # text_content = re.sub(r'<(.*?)>', '', html)
                # ReplyMail.objects.create(campaign_log=campaign_log,
                #                          reply_from=campaign.created_by.email,
                #                          text=text_content,
                #                          sent_on=datetime.datetime.now())
                send_campaign_mail(
                    subject, mail_html, from_email, [each_contact.email], [], [reply_to_email], [])
    except Exception as e:
        print (e)
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
        contact = Contact.objects.filter(email=each['email']).first()
        if contact:
            contact.is_bounced = True
            contact.save()

    bounces = requests.get('https://api.sendgrid.com/api/unsubscribes.get.json?api_user=' +
                           settings.EMAIL_HOST_USER + '&api_key=' + settings.EMAIL_HOST_PASSWORD)
    for each in bounces.json():
        contact = Contact.objects.filter(email=each['email']).first()
        if contact:
            contact.is_unsubscribed = True
            contact.save()


@task
def send_scheduled_campaigns():
    from datetime import datetime
    campaigns = Campaign.objects.filter(schedule_date_time__isnull=False)
    for each in campaigns:
        sent_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sent_time = datetime.strptime(sent_time, '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone('UTC')
        schedule_date_time_hour = str(each.schedule_date_time.time()).replace(':00:00', '')
        sent_time = local_tz.localize(sent_time)
        sent_time = convert_to_custom_timezone(sent_time, each.timezone)
        if (
            str(each.schedule_date_time.date()) == str(sent_time.date()) and
            str(schedule_date_time_hour) == str(sent_time.hour)
        ):
            run_campaign(each)
