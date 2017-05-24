from django.db import models
from accounts.models import LeadAccount
from contacts.models import Contact
from django.utils.translation import pgettext_lazy
from planner.models import Event
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType


class Case(models.Model):
    statusChoice = (("New", "New"),
                    ('Assigned', 'Assigned'),
                    ('Pending', 'Pending'),
                    ('Closed', 'Closed'),
                    ('Rejected', 'Rejected'),
                    ('Duplicate', 'Duplicate'),)
    priorityChoice = (("Low", "Low"),
                      ('Normal', 'Normal'),
                      ('High', 'High'),
                      ('Urgent', 'Urgent'),)
    typeChoice = (("Question", "Question"),
                  ('Incident', 'Incident'),
                  ('Problem', 'Problem'),)
    teamsChoice = (("Sales", "Sales"),
                   ('Support', 'Support'),
                   ('TopManagement', 'TopManagement'),)
    name = models.CharField(
        pgettext_lazy(u"Name of the case", u"Name"),
        max_length=64)
    case_type = models.CharField(choices=typeChoice, max_length=255, blank=True, null=True, default='')
    status = models.CharField(choices=statusChoice, max_length=64, blank=True, null=True, default='')
    account = models.ForeignKey(LeadAccount, blank=True, null=True, default='')
    contacts = models.ManyToManyField(Contact, blank=True)
    priority = models.CharField(choices=priorityChoice, max_length=64, blank=True, null=True, default='')
    description = models.TextField(null=True, blank=True)
    teams = models.CharField(choices=teamsChoice, max_length=64, blank=True, null=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    userid = models.ForeignKey(User, on_delete=models.CASCADE, default='', blank=True, null=True)
    assigned_user = models.CharField(max_length=255, blank=True, null=True, default='')

    def __str__(self):
        return self.name

    def get_meetings(self):
        content_type = ContentType.objects.get(app_label="cases", model="case")
        return Event.objects.filter(content_type=content_type, object_id=self.id, event_type="Meeting", status="Planned")

    def get_completed_meetings(self):
        content_type = ContentType.objects.get(app_label="cases", model="case")
        return Event.objects.filter(content_type=content_type, object_id=self.id, event_type="Meeting").exclude(status="Planned")

    def get_tasks(self):
        content_type = ContentType.objects.get(app_label="cases", model="case")
        return Event.objects.filter(content_type=content_type, object_id=self.id, event_type="Task", status="Planned")

    def get_completed_tasks(self):
        content_type = ContentType.objects.get(app_label="cases", model="case")
        return Event.objects.filter(content_type=content_type, object_id=self.id, event_type="Task").exclude(status="Planned")

    def get_calls(self):
        content_type = ContentType.objects.get(app_label="cases", model="case")
        return Event.objects.filter(content_type=content_type, object_id=self.id, event_type="Call", status="Planned")

    def get_completed_calls(self):
        content_type = ContentType.objects.get(app_label="cases", model="case")
        return Event.objects.filter(content_type=content_type, object_id=self.id, event_type="Call").exclude(status="Planned")

    def get_assigned_user(self):
        return User.objects.get(id=self.assigned_user)


class Comments(models.Model):
    caseid = models.ForeignKey(Case, blank=True, null=True, related_name="cases", on_delete=models.CASCADE, default='')
    comment = models.CharField(max_length=255)
    comment_time = models.DateTimeField(auto_now_add=True)
    comment_user = models.ForeignKey(User, on_delete=models.CASCADE, default='', blank=True, null=True)

    def get_files(self):
        return Comment_Files.objects.filter(comment_id=self)


class Comment_Files(models.Model):
    comment_id = models.ForeignKey(Comments, on_delete=models.CASCADE, default='')
    updated = models.DateTimeField(auto_now_add=True)
    comment_file = models.FileField("File", upload_to="media/comment_files", default='')

    def get_file_id(self):
        if self.comment_file:
            return self.id
        else:
            return None

    def get_file(self):
        if self.comment_file:
            return self.comment_file.path.split('/')[-1]
        else:
            return None
