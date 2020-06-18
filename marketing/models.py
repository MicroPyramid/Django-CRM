import arrow
import os
from datetime import datetime, timedelta
from django.db import models
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.dispatch import receiver
from django.db.models import Sum
from django.template.defaultfilters import slugify
from common.models import User
from common.utils import convert_to_custom_timezone


class Tag(models.Model):
    name = models.CharField(max_length=500)
    color = models.CharField(max_length=20,
                             default="#999999", verbose_name=_("color"))
    created_by = models.ForeignKey(User,
                                   related_name="marketing_tags",
                                   null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)

    @property
    def created_by_user(self):
        return self.created_by if self.created_by else None


class EmailTemplate(models.Model):
    created_by = models.ForeignKey(
        User, related_name="marketing_emailtemplates",
        null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=5000)
    subject = models.CharField(max_length=5000)
    html = models.TextField()

    class Meta:
        ordering = ['id', ]

    @property
    def created_by_user(self):
        return self.created_by if self.created_by else None

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()


class ContactList(models.Model):
    created_by = models.ForeignKey(
        User, related_name="marketing_contactlist",
        null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=500)
    tags = models.ManyToManyField(Tag)
    # is_public = models.BooleanField(default=False)
    visible_to = models.ManyToManyField(
        User, related_name="contact_lists_visible_to")

    class Meta:
        ordering = ('-created_on',)

    @property
    def created_by_user(self):
        return self.created_by if self.created_by else None

    @property
    def created_on_format(self):
        return self.created_on.strftime('%b %d, %Y %I:%M %p')

    # @property
    # def created_on_since(self):
    #     now = datetime.now()
    #     difference = now.replace(tzinfo=None) - \
    #         self.created_on.replace(tzinfo=None)

    #     if difference <= timedelta(minutes=1):
    #         return 'just now'
    #     return '%(time)s ago' % {
    #         'time': timesince(self.created_on).split(', ')[0]}

    @property
    def tags_data(self):
        return self.tags.all()

    @property
    def no_of_contacts(self):
        return self.contacts.all().count()

    @property
    def no_of_campaigns(self):
        return self.campaigns.all().count()

    @property
    def unsubscribe_contacts(self):
        return self.contacts.filter(is_unsubscribed=True).count()

    @property
    def bounced_contacts(self):
        return self.contacts.filter(is_bounced=True).count()

    # @property
    # def no_of_clicks(self):
    #     clicks = CampaignLog.objects.filter(
    #         contact__contact_list__in=[self]).aggregate(Sum(
    #             'no_of_clicks'))['no_of_clicks__sum']
    #     return clicks

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

    @property
    def updated_on_arrow(self):
        return arrow.get(self.updated_on).humanize()


class Contact(models.Model):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. \
        Up to 20 digits allowed."
    )
    created_by = models.ForeignKey(
        User, related_name="marketing_contacts_created_by",
        null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    contact_list = models.ManyToManyField(ContactList, related_name="contacts")
    name = models.CharField(max_length=500)
    email = models.EmailField()
    contact_number = models.CharField(
        validators=[phone_regex], max_length=20, blank=True, null=True)
    is_unsubscribed = models.BooleanField(default=False)
    is_bounced = models.BooleanField(default=False)
    company_name = models.CharField(max_length=500, null=True, blank=True)
    last_name = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=500, null=True, blank=True)
    state = models.CharField(max_length=500, null=True, blank=True)
    contry = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.email

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

    class Meta:
        ordering = ['id', ]


class FailedContact(models.Model):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'.\
        Up to 20 digits allowed."
    )
    created_by = models.ForeignKey(
        User, related_name="marketing_failed_contacts_created_by", null=True,
        on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    contact_list = models.ManyToManyField(
        ContactList, related_name="failed_contacts")
    name = models.CharField(max_length=500, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    contact_number = models.CharField(
        validators=[phone_regex], max_length=20, blank=True, null=True)
    company_name = models.CharField(max_length=500, null=True, blank=True)
    last_name = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=500, null=True, blank=True)
    state = models.CharField(max_length=500, null=True, blank=True)
    contry = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.email

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()


def get_campaign_attachment_path(self, filename):
    file_split = filename.split('.')
    file_extension = file_split[-1]
    path = "%s_%s" % (file_split[0], str(datetime.now()))
    return "campaigns/attachment/" + slugify(path) + "." + file_extension


class Campaign(models.Model):
    STATUS_CHOICES = (
        ('Scheduled', 'Scheduled'),
        ('Cancelled', 'Cancelled'),
        ('Sending', 'Sending'),
        ('Preparing', 'Preparing'),
        ('Sent', 'Sent'),
    )

    title = models.CharField(max_length=5000)
    created_by = models.ForeignKey(
        User, related_name="marketing_campaigns_created_by",
        null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    contact_lists = models.ManyToManyField(
        ContactList, related_name="campaigns")
    email_template = models.ForeignKey(
        EmailTemplate, blank=True, null=True, on_delete=models.SET_NULL)
    schedule_date_time = models.DateTimeField(blank=True, null=True)
    timezone = models.CharField(max_length=100, default='UTC')
    reply_to_email = models.EmailField(blank=True, null=True)
    subject = models.CharField(max_length=5000)
    html = models.TextField()
    html_processed = models.TextField(default="", blank=True)
    from_email = models.EmailField(blank=True, null=True)
    from_name = models.EmailField(blank=True, null=True)
    sent = models.IntegerField(default='0', blank=True)
    opens = models.IntegerField(default='0', blank=True)
    opens_unique = models.IntegerField(default='0', blank=True)
    bounced = models.IntegerField(default='0')
    tags = models.ManyToManyField(Tag)
    status = models.CharField(
        default="Preparing", choices=STATUS_CHOICES, max_length=20)
    attachment = models.FileField(
        max_length=1000, upload_to=get_campaign_attachment_path, blank=True, null=True)

    class Meta:
        ordering = ('-created_on', )

    # @property
    # def no_of_unsubscribers(self):
    #     unsubscribers = self.campaign_contacts.filter(
    #         contact__is_unsubscribed=True).count()
    #     return unsubscribers

    # @property
    # def no_of_bounces(self):
    #     bounces = self.campaign_contacts.filter(
    #         contact__is_bounced=True).count()
    #     return bounces

    @property
    def no_of_clicks(self):
        clicks = self.marketing_links.aggregate(Sum('clicks'))['clicks__sum']
        return clicks

    # @property
    # def no_of_sent_emails(self):
    #     contacts = self.campaign_contacts.count()
    #     return contacts

    # @property
    # def created_on_format(self):
    #     return self.created_on.strftime('%b %d, %Y %I:%M %p')

    @property
    def sent_on_format(self):
        if self.schedule_date_time:
            c_schedule_date_time = convert_to_custom_timezone(
                self.schedule_date_time, self.timezone)
            return c_schedule_date_time.strftime('%b %d, %Y %I:%M %p')
        else:
            c_created_on = convert_to_custom_timezone(
                self.created_on, self.timezone)
            return c_created_on.strftime('%b %d, %Y %I:%M %p')

    @property
    def get_all_emails_count(self):
        email_count = CampaignLog.objects.filter(campaign=self).count()
        return email_count
        # return self.contact_lists.exclude(contacts__email=None).values_list('contacts__email').count()

    @property
    def get_all_email_bounces_count(self):
        # return self.contact_lists.filter(contacts__is_bounced=True
        #                                  ).exclude(contacts__email=None).values_list('contacts__email').count()
        email_count = CampaignLog.objects.filter(
            campaign=self, contact__is_bounced=True).count()
        return email_count

    @property
    def get_all_emails_unsubscribed_count(self):
        # return self.contact_lists.filter(contacts__is_unsubscribed=True
        #                                  ).exclude(contacts__email=None).values_list('contacts__email').count()
        email_count = CampaignLog.objects.filter(
            campaign=self, contact__is_unsubscribed=True).count()
        return email_count

    @property
    def get_all_emails_subscribed_count(self):
        return self.get_all_emails_count - self.get_all_email_bounces_count - self.get_all_emails_unsubscribed_count

    @property
    def get_all_emails_contacts_opened(self):
        contact_ids = CampaignOpen.objects.filter(
            campaign=self).values_list('contact_id', flat=True)
        # opened_contacts = Contact.objects.filter(id__in=contact_ids)
        # return opened_contacts
        return contact_ids.count()

    @property
    def sent_on_arrow(self):
        if self.schedule_date_time:
            c_schedule_date_time = convert_to_custom_timezone(
                self.schedule_date_time, self.timezone)
            # return c_schedule_date_time.strftime('%b %d, %Y %I:%M %p')
            return arrow.get(c_schedule_date_time).humanize()
        else:
            c_created_on = convert_to_custom_timezone(
                self.created_on, self.timezone)
            # return c_created_on.strftime('%b %d, %Y %I:%M %p')
            return arrow.get(self.created_on).humanize()


@receiver(models.signals.pre_delete, sender=Campaign)
def comment_attachments_delete(sender, instance, **kwargs):
    attachment = instance.attachment
    if attachment:
        try:
            if os.path.isfile(attachment.path):
                os.remove(attachment.path)
        except Exception:
            return False
    return True


class Link(models.Model):
    campaign = models.ForeignKey(
        Campaign, related_name="marketing_links", on_delete=models.CASCADE)
    original = models.URLField(max_length=2100)
    clicks = models.IntegerField(default='0')
    unique = models.IntegerField(default='0')

    class Meta:
        ordering = ('id',)


class CampaignLog(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    campaign = models.ForeignKey(
        Campaign, related_name='campaign_log_contacts', on_delete=models.CASCADE)
    contact = models.ForeignKey(
        Contact, related_name="marketing_campaign_logs",
        null=True, on_delete=models.SET_NULL)
    message_id = models.CharField(max_length=1000, null=True, blank=True)


class CampaignLinkClick(models.Model):
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="campaign_link_click")
    link = models.ForeignKey(
        Link, blank=True, null=True, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    created_on = models.DateTimeField(auto_now_add=True)
    user_agent = models.CharField(max_length=2000, blank=True, null=True)
    contact = models.ForeignKey(
        Contact, blank=True, null=True, on_delete=models.CASCADE)


class CampaignOpen(models.Model):
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='campaign_open')
    ip_address = models.GenericIPAddressField()
    created_on = models.DateTimeField(auto_now_add=True)
    user_agent = models.CharField(max_length=2000, blank=True, null=True)
    contact = models.ForeignKey(
        Contact, blank=True, null=True, on_delete=models.CASCADE, related_name='contact_campaign_open')


class CampaignCompleted(models.Model):
    """ This Model Is Used To Check If The Scheduled Later Emails Have Been Sent
        related name : campaign_is_completed
    """
    campaign = models.OneToOneField(
        Campaign, on_delete=models.CASCADE, related_name='campaign_is_completed')
    is_completed = models.BooleanField(default=False)


class ContactUnsubscribedCampaign(models.Model):
    """ This Model Is Used To Check If The Contact has Unsubscribed To a Particular Campaign
        related name : contact_is_unsubscribed
    """
    campaigns = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='campaign_is_unsubscribed')
    contacts = models.ForeignKey(
        Contact, on_delete=models.Case, related_name='contact_is_unsubscribed')
    is_unsubscribed = models.BooleanField(default=False)


class ContactEmailCampaign(models.Model):
    """
    send all campaign emails to this contact
    """
    name = models.CharField(max_length=500)
    email = models.EmailField()
    last_name = models.CharField(max_length=500, null=True, blank=True)
    created_by = models.ForeignKey(
        User, related_name="marketing_contacts_emails_campaign_created_by",
        null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)

    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

    class Meta:
        ordering = ('created_on',)


class DuplicateContacts(models.Model):
    """
    this model is used to store duplicate contacts
    """
    contacts = models.ForeignKey(
        Contact, related_name='duplicate_contact', on_delete=models.SET_NULL, null=True)
    contact_list = models.ForeignKey(
        ContactList, related_name='duplicate_contact_contact_list', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ('id', )


class BlockedDomain(models.Model):
    """
        this model is used to block the domain
    """
    domain = models.CharField(max_length=200)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.domain

    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

    class Meta:
        ordering = ('created_on',)


class BlockedEmail(models.Model):
    """
        this model is used to block the email
    """
    email = models.EmailField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.email

    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()
    class Meta:
        ordering = ('created_on',)
