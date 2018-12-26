from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager

from common.utils import COUNTRIES, ROLES
import time


def img_url(self, filename):
    hash_ = int(time.time())
    return "%s/%s/%s" % ("profile_pics", hash_, filename)


class User(AbstractBaseUser, PermissionsMixin):
    file_prepend = "users/profile_pics"
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(('date joined'), auto_now_add=True)
    role = models.CharField(max_length=50, choices=ROLES)
    profile_pic = models.FileField(max_length=1000, upload_to=img_url, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    objects = UserManager()

    def get_short_name(self):
        return self.username

    def __unicode__(self):
        return self.email


class Address(models.Model):
    address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    street = models.CharField(_("Street"), max_length=55, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(_("Post/Zip-code"), max_length=64, blank=True, null=True)
    country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, null=True)

    def __str__(self):
        return self.city if self.city else ""

    def get_complete_address(self):
        address = ""
        if self.address_line:
            address += self.address_line
        if self.street:
            if address:
                address += ", " + self.street
            else:
                address += self.street
        if self.city:
            if address:
                address += ", " + self.city
            else:
                address += self.city
        if self.state:
            if address:
                address += ", " + self.state
            else:
                address += self.state
        if self.postcode:
            if address:
                address += ", " + self.postcode
            else:
                address += self.postcode
        if self.country:
            if address:
                address += ", " + self.get_country_display()
            else:
                address += self.get_country_display()
        return address


class Team(models.Model):
    name = models.CharField(max_length=55)
    members = models.ManyToManyField(User)

    def __str__(self):
        return self.name


class Comment(models.Model):
    case = models.ForeignKey('cases.Case', blank=True, null=True, related_name="cases", on_delete=models.CASCADE)
    comment = models.CharField(max_length=255)
    commented_on = models.DateTimeField(auto_now_add=True)
    commented_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    account = models.ForeignKey(
        'accounts.Account', blank=True, null=True, related_name="accounts_comments", on_delete=models.CASCADE)
    lead = models.ForeignKey('leads.Lead', blank=True, null=True, related_name="leads", on_delete=models.CASCADE)
    opportunity = models.ForeignKey(
        'opportunity.Opportunity', blank=True, null=True, related_name="opportunity_comments", on_delete=models.CASCADE)
    contact = models.ForeignKey(
        'contacts.Contact', blank=True, null=True, related_name="contact_comments", on_delete=models.CASCADE)

    def get_files(self):
        return Comment_Files.objects.filter(comment_id=self)


class Comment_Files(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    updated_on = models.DateTimeField(auto_now_add=True)
    comment_file = models.FileField("File", upload_to="comment_files", default='')

    def get_file_name(self):
        if self.comment_file:
            return self.comment_file.path.split('/')[-1]
        else:
            return None


class Attachments(models.Model):
    created_by = models.ForeignKey(User, related_name='attachment_created_by', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=60)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    attachment = models.FileField(max_length=1001, upload_to='attachments/%Y/%m/')
    lead = models.ForeignKey('leads.Lead', null=True, blank=True, related_name='lead_attachment', on_delete=models.CASCADE)
    account = models.ForeignKey('accounts.Account', null=True, blank=True, related_name='account_attachment', on_delete=models.CASCADE)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='contact_attachment', blank=True, null=True)
    opportunity = models.ForeignKey('opportunity.Opportunity',blank=True,null=True,on_delete=models.CASCADE,related_name='opportunity_attachment')
