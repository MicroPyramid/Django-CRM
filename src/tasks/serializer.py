from rest_framework import serializers
from tasks.models import Task
from common.serializer import (
    ProfileSerializer,
    AttachmentsSerializer,
    CommentSerializer,
)
from contacts.serializer import ContactSerializer
from teams.serializer import TeamsSerializer


class TaskSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer()
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
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
        )


class TaskCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.org

        self.fields["title"].required = True

    def validate_title(self, title):
        if self.instance:
            if (
                Task.objects.filter(title__iexact=title, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Task already exists with this title")
        else:
            if Task.objects.filter(title__iexact=title, org=self.org).exists():
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
        )
