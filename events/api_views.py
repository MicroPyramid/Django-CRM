from django.db.models import Q
from contacts.models import Contact
from contacts.serializer import ContactSerializer

from common.models import User, Attachments, Comment
from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import (
    UserSerializer,
    CommentSerializer,
    AttachmentsSerializer,
    CommentSerializer,
)
from events import swagger_params
from events.models import Event
from events.serializer import EventSerializer, EventCreateSerializer
from events.tasks import send_email

from teams.serializer import TeamsSerializer
from teams.models import Teams
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from drf_yasg.utils import swagger_auto_schema
import json
from datetime import datetime, timedelta

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
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.all()
        contacts = Contact.objects.all()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user)
            )
            contacts = contacts.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            ).distinct()

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))
            if params.get("created_by"):
                queryset = queryset.filter(created_by=params.get("created_by"))
            if params.getlist("assigned_users"):
                queryset = queryset.filter(
                    assigned_to__id__in=json.loads(params.get("assigned_users"))
                )
            if params.get("date_of_meeting"):
                queryset = queryset.filter(
                    date_of_meeting=params.get("date_of_meeting")
                )
        context = {}
        search = False
        if (
            params.get("name")
            or params.get("created_by")
            or params.get("assigned_users")
            or params.get("date_of_meeting")
        ):
            search = True
        context["search"] = search
        results_events = self.paginate_queryset(queryset, self.request, view=self)
        events = EventSerializer(results_events, many=True).data

        context["per_page"] = 10
        context.update(
            {
                "events_count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_number": int(self.offset / 10) + 1,
            }
        )

        if search:
            context["events"] = events
            return context

        context["events"] = events
        users = []
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            users = User.objects.filter(
                is_active=True,
            ).order_by("email")
        else:
            users = User.objects.filter(role="ADMIN").order_by("email")
        context["recurring_days"] = WEEKDAYS
        context["users"] = UserSerializer(users, many=True).data
        if self.request.user == "ADMIN":
            context["teams_list"] = TeamsSerializer(Teams.objects.all(), many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        return context

    @swagger_auto_schema(
        tags=["Events"], manual_parameters=swagger_params.event_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Events"], manual_parameters=swagger_params.event_create_post_params
    )
    def post(self, request, *args, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        data = {}
        serializer = EventCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            recurring_days = json.dumps(params.get("recurring_days"))
            if params.get("event_type") == "Non-Recurring":
                event_obj = serializer.save(
                    created_by=request.user,
                    date_of_meeting=params.get("start_date"),
                    is_active=True,
                    disabled=False,
                )
                if params.get("contacts"):
                    contacts = json.loads(params.get("contacts"))
                    for contact in contacts:
                        obj_contact = Contact.objects.filter(id=contact)
                        if obj_contact.exists():
                            event_obj.contacts.add(contact)
                        else:
                            event_obj.delete()
                            data["contacts"] = "Please enter valid contact"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                if self.request.user.role == "ADMIN":
                    if params.get("teams"):
                        teams = json.loads(params.get("teams"))
                        for team in teams:
                            teams_ids = Teams.objects.filter(id=team)
                            if teams_ids.exists():
                                event_obj.teams.add(team)
                            else:
                                event_obj.delete()
                                data["team"] = "Please enter valid Team"
                                return Response(
                                    {"error": True, "errors": data},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                    if params.get("assigned_to"):
                        assinged_to_users_ids = json.loads(params.get("assigned_to"))
                        for user_id in assinged_to_users_ids:
                            user = User.objects.filter(id=user_id)
                            if user.exists():
                                event_obj.assigned_to.add(user_id)
                            else:
                                event_obj.delete()
                                data["assigned_to"] = "Please enter valid User"
                                return Response(
                                    {"error": True, "errors": data},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                assigned_to_list = list(
                    event_obj.assigned_to.all().values_list("id", flat=True)
                )
                send_email.delay(
                    event_obj.id,
                    assigned_to_list,
                    domain=request.get_host(),
                    protocol=request.scheme,
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
                        created_by=request.user,
                        start_date=start_date,
                        end_date=end_date,
                        name=data["name"],
                        event_type=data["event_type"],
                        description=data["description"],
                        start_time=data["start_time"],
                        end_time=data["end_time"],
                        date_of_meeting=each,
                    )

                    if params.get("contacts"):
                        contacts = json.loads(params.get("contacts"))
                        for contact in contacts:
                            obj_contact = Contact.objects.filter(id=contact)
                            if obj_contact.exists():
                                event.contacts.add(contact)
                            else:
                                event.delete()
                                data["contacts"] = "Please enter valid contact"
                                return Response(
                                    {"error": True, "errors": data},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                    if self.request.user.role == "ADMIN":
                        if params.get("teams"):
                            teams = json.loads(params.get("teams"))
                            for team in teams:
                                teams_ids = Teams.objects.filter(id=team)
                                if teams_ids.exists():
                                    event.teams.add(team)
                                else:
                                    event.delete()
                                    data["team"] = "Please enter valid Team"
                                    return Response(
                                        {"error": True, "errors": data},
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )
                        if params.get("assigned_to"):
                            assinged_to_users_ids = json.loads(
                                params.get("assigned_to")
                            )
                            for user_id in assinged_to_users_ids:
                                user = User.objects.filter(id=user_id)
                                if user.exists():
                                    event.assigned_to.add(user_id)
                                else:
                                    event.delete()
                                    data["assigned_to"] = "Please enter valid User"
                                    return Response(
                                        {"error": True, "errors": data},
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )
                    assigned_to_list = list(
                        event.assigned_to.all().values_list("id", flat=True)
                    )
                    send_email.delay(
                        event.id,
                        assigned_to_list,
                        domain=request.get_host(),
                        protocol=request.scheme,
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
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Event.objects.get(pk=pk)

    def get_context_data(self, **kwargs):
        context = {}
        user_assgn_list = [
            assigned_to.id for assigned_to in self.event_obj.assigned_to.all()
        ]
        if self.request.user == self.event_obj.created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comments = Comment.objects.filter(event=self.event_obj).order_by("-id")
        attachments = Attachments.objects.filter(event=self.event_obj).order_by("-id")
        assigned_data = self.event_obj.assigned_to.values("id", "email")
        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            users_mention = list(
                User.objects.filter(
                    is_active=True,
                ).values("username")
            )
        elif self.request.user != self.event_obj.created_by:
            users_mention = [{"username": self.event_obj.created_by.username}]
        else:
            users_mention = list(self.event_obj.assigned_to.all().values("username"))
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            users = User.objects.filter(
                is_active=True,
            ).order_by("email")
        else:
            users = User.objects.filter(
                role="ADMIN",
            ).order_by("email")

        if self.request.user == self.event_obj.created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        team_ids = [user.id for user in self.event_obj.get_team_users]
        all_user_ids = users.values_list("id", flat=True)
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = User.objects.filter(id__in=users_excluding_team_id)

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

        context["users"] = UserSerializer(users, many=True).data
        context["users_excluding_team"] = UserSerializer(
            users_excluding_team, many=True
        ).data
        context["teams"] = TeamsSerializer(Teams.objects.all(), many=True).data
        return context

    @swagger_auto_schema(
        tags=["Events"],
    )
    def get(self, request, pk, **kwargs):
        self.event_obj = self.get_object(pk)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Events"], manual_parameters=swagger_params.event_detail_post_params
    )
    def post(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        context = {}
        self.event_obj = Event.objects.get(pk=pk)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.event_obj.created_by)
                or (self.request.user in self.event_obj.assigned_to.all())
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
                    commented_by_id=self.request.user.id,
                )

        if self.request.FILES.get("event_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.user
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

    @swagger_auto_schema(
        tags=["Events"], manual_parameters=swagger_params.event_create_post_params
    )
    def put(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        data = {}
        self.event_obj = self.get_object(pk)
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
                contacts = json.loads(params.get("contacts"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact)
                    if obj_contact.exists():
                        event_obj.contacts.add(contact)
                    else:
                        data["contacts"] = "Please enter valid Contact"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            if self.request.user.role == "ADMIN":
                event_obj.teams.clear()
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team)
                        if teams_ids.exists():
                            event_obj.teams.add(team)
                        else:
                            event_obj.delete()
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                else:
                    event_obj.teams.clear()

                event_obj.assigned_to.clear()
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id)
                        if user.exists():
                            event_obj.assigned_to.add(user_id)
                        else:
                            event_obj.delete()
                            data["assigned_to"] = "Please enter valid User"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                else:
                    event_obj.assigned_to.clear()
            assigned_to_list = list(
                event_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email.delay(
                event_obj.id,
                recipients,
                domain=request.get_host(),
                protocol=request.scheme,
            )
            return Response(
                {"error": False, "message": "Event updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Events"],
    )
    def delete(self, request, pk, **kwargs):
        self.object = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.created_by
        ):
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
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Events"], manual_parameters=swagger_params.event_comment_edit_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        obj = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params)
            if params.get("comment"):
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
        else:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have Permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(
        tags=["Events"],
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.commented_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Comment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have Permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class EventAttachmentView(APIView):
    model = Attachments
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Events"],
    )
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have Permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
