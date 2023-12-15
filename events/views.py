import json
from datetime import datetime, timedelta

from django.db.models import Q
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Attachments, Comment, Profile, User

#from common.external_auth import CustomDualAuthentication
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    ProfileSerializer
)
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from events import swagger_params1
from events.models import Event
from events.serializer import EventCreateSerializer, EventSerializer, EventCreateSwaggerSerializer, EventDetailEditSwaggerSerializer, EventCommentEditSwaggerSerializer
from events.tasks import send_email
from teams.models import Teams
from teams.serializer import TeamsSerializer

WEEKDAYS = (
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
)


class EventListView(APIView, LimitOffsetPagination):
    model = Event
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        contacts = Contact.objects.filter(org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile])
                | Q(created_by=self.request.profile.user)
            )
            contacts = contacts.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))
            if params.get("created_by"):
                queryset = queryset.filter(created_by=params.get("created_by"))
            if params.getlist("assigned_users"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.get("assigned_users")
                )
            if params.get("date_of_meeting"):
                queryset = queryset.filter(
                    date_of_meeting=params.get("date_of_meeting")
                )
        context = {}
        results_events = self.paginate_queryset(queryset, self.request, view=self)
        events = EventSerializer(results_events, many=True).data
        if results_events:
            offset = queryset.filter(id__gte=results_events[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context.update({"events_count": self.count, "offset": offset})
        context["events"] = events
        context["recurring_days"] = WEEKDAYS
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        return context

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.event_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params,request=EventCreateSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        data = {}
        serializer = EventCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            recurring_days = json.dumps(params.get("recurring_days"))
            if params.get("event_type") == "Non-Recurring":
                event_obj = serializer.save(
                    created_by=request.profile.user,
                    date_of_meeting=params.get("start_date"),
                    is_active=True,
                    disabled=False,
                    org=request.profile.org,
                )

                if params.get("contacts"):
                    obj_contact = Contact.objects.filter(
                        id=params.get("contacts"), org=request.profile.org
                    )
                    event_obj.contacts.add(obj_contact)

                if params.get("teams"):
                    teams_list = params.get("teams")
                    teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                    event_obj.teams.add(*teams)

                if params.get("assigned_to"):
                    assinged_to_list = params.get("assigned_to")
                    profiles = Profile.objects.filter(
                        id__in=assinged_to_list, org=request.profile.org
                    )
                    event_obj.assigned_to.add(*profiles)

                assigned_to_list = list(
                    event_obj.assigned_to.all().values_list("id", flat=True)
                )
                send_email.delay(
                    event_obj.id,
                    assigned_to_list,
                )
            if params.get("event_type") == "Recurring":
                recurring_days = params.get("recurring_days")
                if not recurring_days:
                    return Response(
                        {"error": True, "errors": "Choose atleast one recurring day"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

                delta = end_date - start_date
                required_dates = []

                for day in range(delta.days + 1):
                    each_date = start_date + timedelta(days=day)
                    if each_date.strftime("%A") in recurring_days:
                        required_dates.append(each_date)

                for each in required_dates:
                    each = datetime.strptime(str(each), "%Y-%m-%d").date()
                    data = serializer.validated_data

                    event = Event.objects.create(
                        created_by=request.profile.user,
                        start_date=start_date,
                        end_date=end_date,
                        name=data["name"],
                        event_type=data["event_type"],
                        description=data["description"],
                        start_time=data["start_time"],
                        end_time=data["end_time"],
                        date_of_meeting=each,
                        org=request.profile.org,
                    )

                    if params.get("contacts"):
                        obj_contact = Contact.objects.filter(
                            id=params.get("contacts"), org=request.profile.org
                        )
                        event.contacts.add(obj_contact)

                    if params.get("teams"):
                        teams_list = params.get("teams")
                        teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                        event.teams.add(*teams)

                    if params.get("assigned_to"):
                        assinged_to_list = params.get("assigned_to")
                        profiles = Profile.objects.filter(
                            id__in=assinged_to_list, org=request.profile.org
                        )
                        event.assigned_to.add(*profiles)

                    assigned_to_list = list(
                        event.assigned_to.all().values_list("id", flat=True)
                    )
                    send_email.delay(
                        event.id,
                        assigned_to_list,
                    )
            return Response(
                {"error": False, "message": "Event Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class EventDetailView(APIView):
    model = Event
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Event.objects.get(pk=pk)

    def get_context_data(self, **kwargs):
        context = {}
        user_assgn_list = [
            assigned_to.id for assigned_to in self.event_obj.assigned_to.all()
        ]
        if self.request.profile == self.event_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comments = Comment.objects.filter(event=self.event_obj).order_by("-id")
        attachments = Attachments.objects.filter(event=self.event_obj).order_by("-id")
        assigned_data = self.event_obj.assigned_to.values("id", "user__email")
        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(
                    is_active=True,
                ).values("user__email")
            )
        elif self.request.profile != self.event_obj.created_by:
            users_mention = [{"username": self.event_obj.created_by.user.email}]
        else:
            users_mention = list(
                self.event_obj.assigned_to.all().values("user__email")
            )
        profile_list = Profile.objects.filter(is_active=True, org=self.request.profile.org)
        if self.request.profile.role == "ADMIN" or self.request.profile.is_admin:
            profiles = profile_list.order_by("user__email")
        else:
            profiles = profile_list.filter(role="ADMIN").order_by("user__email")

        if self.request.profile == self.event_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        team_ids = [user.id for user in self.event_obj.get_team_users]
        all_user_ids = profiles.values_list("id", flat=True)
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = Profile.objects.filter(id__in=users_excluding_team_id)

        selected_recurring_days = Event.objects.filter(
            name=self.event_obj.name
        ).values_list("date_of_meeting", flat=True)
        selected_recurring_days = set(
            [day.strftime("%A") for day in selected_recurring_days]
        )
        context.update(
            {
                "event_obj": EventSerializer(self.event_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "selected_recurring_days": selected_recurring_days,
                "users_mention": users_mention,
                "assigned_data": assigned_data,
            }
        )

        context["users"] = ProfileSerializer(profiles, many=True).data
        context["users_excluding_team"] = ProfileSerializer(
            users_excluding_team, many=True
        ).data
        context["teams"] = TeamsSerializer(Teams.objects.all(), many=True).data
        return context

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params
    )
    def get(self, request, pk, **kwargs):
        self.event_obj = self.get_object(pk)
        if self.event_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params,request=EventDetailEditSwaggerSerializer
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        context = {}
        self.event_obj = Event.objects.get(pk=pk)
        if self.event_obj.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.event_obj.created_by)
                or (self.request.profile in self.event_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        comment_serializer = CommentSerializer(data=params)
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    event_id=self.event_obj.id,
                    commented_by_id=self.request.profile.id,
                )

        if self.request.FILES.get("event_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile.user
            attachment.file_name = self.request.FILES.get("event_attachment").name
            attachment.event = self.event_obj
            attachment.attachment = self.request.FILES.get("event_attachment")
            attachment.save()

        comments = Comment.objects.filter(event__id=self.event_obj.id).order_by("-id")
        attachments = Attachments.objects.filter(event__id=self.event_obj.id).order_by(
            "-id"
        )
        context.update(
            {
                "event_obj": EventSerializer(self.event_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params,request=EventCreateSwaggerSerializer
    )
    def put(self, request, pk, **kwargs):
        params = request.data
        data = {}
        self.event_obj = self.get_object(pk)
        if self.event_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = EventCreateSerializer(
            data=params,
            instance=self.event_obj,
            request_obj=request,
        )
        if serializer.is_valid():
            event_obj = serializer.save()
            previous_assigned_to_users = list(
                event_obj.assigned_to.all().values_list("id", flat=True)
            )
            if params.get("event_type") == "Non-Recurring":
                event_obj.date_of_meeting = event_obj.start_date

            event_obj.contacts.clear()
            if params.get("contacts"):
                obj_contact = Contact.objects.filter(
                    id=params.get("contacts"), org=request.profile.org
                )
                event_obj.contacts.add(obj_contact)

            event_obj.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                event_obj.teams.add(*teams)

            event_obj.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org
                )
                event_obj.assigned_to.add(*profiles)

            assigned_to_list = list(
                event_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email.delay(
                event_obj.id,
                recipients,
            )
            return Response(
                {"error": False, "message": "Event updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, **kwargs):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == self.object.created_by
        ) and self.object.org == request.profile.org:
            self.object.delete()
            return Response(
                {"error": False, "message": "Event deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": "you don't have permission to delete this event"},
            status=status.HTTP_403_FORBIDDEN,
        )


class EventCommentView(APIView):
    model = Comment
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params,request=EventCommentEditSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"error": False, "message": "Comment Submitted"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have Permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == self.object.commented_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Comment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have Permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class EventAttachmentView(APIView):
    model = Attachments
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Events"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have Permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
