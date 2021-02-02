from rest_framework import serializers
from tasks.models import Task
from common.serializer import (
    UserSerializer,
    AttachmentsSerializer,
    CommentSerializer,
    CompanySerializer,
)
from contacts.serializer import ContactSerializer
from teams.serializer import TeamsSerializer


class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    assigned_to = UserSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    company = CompanySerializer()
    task_attachment = AttachmentsSerializer(read_only=True, many=True)
    task_comments = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "priority",
            "due_date",
            "account",
            "created_by",
            "created_on",
            "contacts",
            "teams",
            "assigned_to",
            "task_attachment",
            "task_comments",
            "company",
        )


class TaskCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(TaskCreateSerializer, self).__init__(*args, **kwargs)

        self.fields["title"].required = True
        self.company = request_obj.company

    def validate_title(self, title):
        if self.instance:
            if (
                Task.objects.filter(
                    title__iexact=title,
                    company=self.company,
                )
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Task already exists with this title")
        else:
            if Task.objects.filter(title__iexact=title, company=self.company).exists():
                raise serializers.ValidationError("Task already exists with this title")
        return title

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "status",
            "priority",
            "due_date",
            "account",
            "created_by",
            "created_on",
            "company",
        )
