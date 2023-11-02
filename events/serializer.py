from datetime import datetime, timedelta

from rest_framework import serializers

from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    UserSerializer
)
from contacts.serializer import ContactSerializer
from events.models import Event
from teams.serializer import TeamsSerializer


class EventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    event_attachment = AttachmentsSerializer(read_only=True, many=True)
    event_comments = CommentSerializer(read_only=True, many=True)
    org = OrganizationSerializer()

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "event_type",
            "status",
            "is_active",
            "disabled",
            "start_date",
            "start_time",
            "end_date",
            "end_time",
            "description",
            "date_of_meeting",
            "created_by",
            "created_at",
            "contacts",
            "teams",
            "assigned_to",
            "event_attachment",
            "event_comments",
            "org",
        )


class EventCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(EventCreateSerializer, self).__init__(*args, **kwargs)
        self.fields["event_type"].required = True
        self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if (
                Event.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Event already exists with this name")
        else:
            if Event.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError("Event already exists with this name")
        return name

    def validate_event_type(self, event_type):
        """This Validation Is For Keeping The Field Readonly While Editing or Updating"""
        event_type = self.initial_data.get("event_type")
        if self.instance:
            return self.instance.event_type
        else:
            return event_type

    def validate_start_date(self, start_date):
        if start_date:
            if self.instance:
                return self.instance.start_date
            else:
                return start_date
        else:
            raise serializers.ValidationError("Enter a valid Start date.")

    def validate_end_date(self, end_date):
        end_date = self.initial_data.get("end_date")
        start_date = self.initial_data.get("start_date")
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        event_type = self.initial_data.get("event_type")
        if event_type == "Recurring":
            if start_date == end_date:
                raise serializers.ValidationError(
                    "Start Date and End Date cannot be equal for recurring events"
                )
        if start_date > end_date:
            raise serializers.ValidationError("End Date cannot be less than start date")
        return end_date

    def validate_end_time(self, end_time):
        end_time = self.initial_data.get("end_time")
        start_time = self.initial_data.get("start_time")
        end_time = datetime.strptime(end_time, "%H:%M:%S").time()
        start_time = datetime.strptime(start_time, "%H:%M:%S").time()
        if not start_time:
            raise serializers.ValidationError("Enter a valid start time.")
        if start_time > end_time:
            raise serializers.ValidationError("End Time cannot be less than Start Time")
        return end_time

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "event_type",
            "start_date",
            "start_time",
            "end_date",
            "end_time",
            "status",
            "is_active",
            "disabled",
            "description",
            "created_by",
            "created_at",
            "org",
        )

class EventCreateSwaggerSerializer(serializers.ModelSerializer):

    recurring_days =  serializers.CharField()
    class Meta:
        model = Event
        fields = (
            "name",
            "event_type",
            "contacts",
            "start_date",
            "start_time",
            "end_date",
            "end_time",
            "teams",
            "assigned_to",
            "description",
            "recurring_days"
        )

class EventDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    event_attachment = serializers.FileField()

class EventCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
