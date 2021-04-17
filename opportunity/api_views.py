import pytz
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q
from opportunity.models import Opportunity
from opportunity.tasks import send_email_to_assigned_user
from opportunity import swagger_params
from opportunity.serializer import (
    OpportunitySerializer,
    TagsSerializer,
    OpportunityCreateSerializer,
)
from accounts.models import Account, Tags
from accounts.serializer import AccountSerializer
from common.models import User, Attachments, Comment
from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import (
    UserSerializer,
    CommentSerializer,
    AttachmentsSerializer,
    LeadCommentSerializer,
)
from common.utils import (
    STAGES,
    SOURCES,
    CURRENCY_CODES,
)
from contacts.models import Contact
from leads.models import Lead
from opportunity.models import SOURCES, STAGES, Opportunity
from contacts.serializer import ContactSerializer
from teams.serializer import TeamsSerializer
from opportunity.serializer import OpportunitySerializer
from teams.models import Teams

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from drf_yasg.utils import swagger_auto_schema
import json
from crm import settings


class OpportunityListView(APIView, LimitOffsetPagination):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Opportunity

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.all()
        accounts = Account.objects.all()
        contacts = Contact.objects.all()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            ).distinct()
            accounts = accounts.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            ).distinct()

        if params:
            request_post = params
            if request_post.get("name"):
                queryset = queryset.filter(name__icontains=request_post.get("name"))
            if request_post.get("account"):
                queryset = queryset.filter(account=request_post.get("account"))
            if request_post.get("stage"):
                queryset = queryset.filter(stage__contains=request_post.get("stage"))
            if request_post.get("lead_source"):
                queryset = queryset.filter(
                    lead_source__contains=request_post.get("lead_source")
                )
            if request_post.get("tags"):
                queryset = queryset.filter(
                    tags__in=json.loads(request_post.get("tags"))
                ).distinct()

        context = {}
        search = False
        if (
            params.get("name")
            or params.get("account")
            or params.get("stage")
            or params.get("lead_source")
            or params.get("tags")
        ):
            search = True
        context["search"] = search

        results_opportunities = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        opportunities = OpportunitySerializer(results_opportunities, many=True).data
        context["per_page"] = 10
        context.update(
            {
                "opportunities_count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_number": int(self.offset / 10) + 1,
            }
        )
        context["opportunities"] = opportunities
        context["users"] = UserSerializer(
            User.objects.filter(is_active=True).order_by("email"),
            many=True,
        ).data
        tag_ids = list(set(Opportunity.objects.all().values_list("tags", flat=True)))
        context["tags"] = TagsSerializer(
            Tags.objects.filter(id__in=tag_ids), many=True
        ).data
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        if self.request.user == "ADMIN":
            context["teams_list"] = TeamsSerializer(Teams.objects.all(), many=True).data
        context["stage"] = STAGES
        context["lead_source"] = SOURCES
        context["currency"] = CURRENCY_CODES

        return context

    @swagger_auto_schema(
        tags=["Opportunities"],
        manual_parameters=swagger_params.opportunity_list_get_params,
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Opportunities"],
        manual_parameters=swagger_params.opportunity_create_post_params,
    )
    def post(self, request, *args, **kwargs):
        params = request.query_params if len(request.data) == 0 else request.data
        data = {}
        serializer = OpportunityCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            opportunity_obj = serializer.save(
                created_by=request.user,
                closed_on=params.get("due_date"),
            )

            if params.get("contacts"):
                contacts = json.loads(params.get("contacts"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact)
                    if obj_contact:
                        opportunity_obj.contacts.add(contact)
                    else:
                        opportunity_obj.delete()
                        data["contacts"] = "Please enter valid contact"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                for tag in tags:
                    obj_tag = Tags.objects.filter(slug=tag.lower())
                    if obj_tag:
                        obj_tag = obj_tag[0]
                    else:
                        obj_tag = Tags.objects.create(name=tag)
                    opportunity_obj.tags.add(obj_tag)

            if params.get("stage"):
                stage = params.get("stage")
                if stage in ["CLOSED WON", "CLOSED LOST"]:
                    opportunity_obj.closed_by = self.request.user

            if self.request.user.role == "ADMIN":
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        obj_team = Teams.objects.filter(id=team)
                        if obj_team:
                            opportunity_obj.teams.add(team)
                        else:
                            opportunity_obj.delete()
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))

                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id)
                        if user:
                            opportunity_obj.assigned_to.add(user_id)
                        else:
                            opportunity_obj.delete()
                            data["assigned_to"] = "Please enter valid user"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.user
                attachment.file_name = self.request.FILES.get(
                    "opportunity_attachment"
                ).name
                attachment.opportunity = opportunity_obj
                attachment.attachment = self.request.FILES.get("opportunity_attachment")
                attachment.save()

            assigned_to_list = list(
                opportunity_obj.assigned_to.all().values_list("id", flat=True)
            )

            recipients = assigned_to_list
            send_email_to_assigned_user.delay(
                recipients,
                opportunity_obj.id,
                domain=settings.Domain,
                protocol=self.request.scheme,
            )
            return Response(
                {"error": False, "message": "Opportunity Created Successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class OpportunityDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Opportunity

    def get_object(self, pk):
        return self.model.objects.filter(id=pk).first()

    @swagger_auto_schema(
        tags=["Opportunities"],
        manual_parameters=swagger_params.opportunity_create_post_params,
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        opportunity_object = self.get_object(pk=pk)
        data = {}
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == opportunity_object.created_by)
                or (self.request.user in opportunity_object.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = OpportunityCreateSerializer(
            opportunity_object,
            data=params,
            request_obj=request,
            opportunity=True,
        )

        if serializer.is_valid():
            opportunity_object = serializer.save(closed_on=params.get("due_date"))
            previous_assigned_to_users = list(
                opportunity_object.assigned_to.all().values_list("id", flat=True)
            )
            opportunity_object.contacts.clear()
            if params.get("contacts"):
                contacts = json.loads(params.get("contacts"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact)
                    if obj_contact:
                        opportunity_object.contacts.add(contact)
                    else:
                        data["contacts"] = "Please enter valid Contact"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            opportunity_object.tags.clear()
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                for tag in tags:
                    obj_tag = Tags.objects.filter(slug=tag.lower())
                    if obj_tag:
                        obj_tag = obj_tag[0]
                    else:
                        obj_tag = Tags.objects.create(name=tag)
                    opportunity_object.tags.add(obj_tag)

            if params.get("stage"):
                stage = params.get("stage")
                if stage in ["CLOSED WON", "CLOSED LOST"]:
                    opportunity_object.closed_by_id = self.request.user.id

            if self.request.user.role == "ADMIN":
                opportunity_object.teams.clear()
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        obj_team = Teams.objects.filter(id=team)
                        if obj_team:
                            opportunity_object.teams.add(team)
                        else:
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                opportunity_object.assigned_to.clear()
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id)
                        if user:
                            opportunity_object.assigned_to.add(user_id)
                        else:
                            data["assigned_to"] = "Please enter valid User"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.user
                attachment.file_name = self.request.FILES.get(
                    "opportunity_attachment"
                ).name
                attachment.opportunity = opportunity_object
                attachment.attachment = self.request.FILES.get("opportunity_attachment")
                attachment.save()

            assigned_to_list = list(
                opportunity_object.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                opportunity_object.id,
                domain=settings.Domain,
                protocol=self.request.scheme,
            )
            return Response(
                {"error": False, "message": "Opportunity Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Opportunities"],
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user != self.object.created_by:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        self.object.delete()
        return Response(
            {"error": False, "message": "Opportunity Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Opportunities"],
    )
    def get(self, request, pk, format=None):
        self.opportunity = self.get_object(pk=pk)
        context = {}
        context["opportunity_obj"] = OpportunitySerializer(self.opportunity).data
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.opportunity.created_by)
                or (self.request.user in self.opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comment_permission = (
            True
            if (
                self.request.user == self.opportunity.created_by
                or self.request.user.is_superuser
                or self.request.user.role == "ADMIN"
            )
            else False
        )

        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            users_mention = list(
                User.objects.filter(
                    is_active=True,
                ).values("username")
            )
        elif self.request.user != self.opportunity.created_by:
            if self.opportunity.created_by:
                users_mention = [{"username": self.opportunity.created_by.username}]
            else:
                users_mention = []
        else:
            users_mention = []

        context.update(
            {
                "comments": CommentSerializer(
                    self.opportunity.opportunity_comments.all(), many=True
                ).data,
                "attachments": AttachmentsSerializer(
                    self.opportunity.opportunity_attachment.all(), many=True
                ).data,
                "contacts": ContactSerializer(
                    self.opportunity.contacts.all(), many=True
                ).data,
                "users": UserSerializer(
                    User.objects.filter(
                        is_active=True,
                    ).order_by("email"),
                    many=True,
                ).data,
                "stage": STAGES,
                "lead_source": SOURCES,
                "currency": CURRENCY_CODES,
                "comment_permission": comment_permission,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @swagger_auto_schema(
        tags=["Opportunities"],
        manual_parameters=swagger_params.opportunity_detail_get_params,
    )
    def post(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        context = {}
        self.opportunity_obj = Opportunity.objects.get(pk=pk)
        comment_serializer = CommentSerializer(data=params)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.opportunity_obj.created_by)
                or (self.request.user in self.opportunity_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    opportunity_id=self.opportunity_obj.id,
                    commented_by_id=self.request.user.id,
                )

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.user
                attachment.file_name = self.request.FILES.get(
                    "opportunity_attachment"
                ).name
                attachment.opportunity = self.opportunity_obj
                attachment.attachment = self.request.FILES.get("opportunity_attachment")
                attachment.save()

        comments = Comment.objects.filter(opportunity=self.opportunity_obj).order_by(
            "-id"
        )
        attachments = Attachments.objects.filter(
            opportunity=self.opportunity_obj
        ).order_by("-id")
        context.update(
            {
                "opportunity_obj": OpportunitySerializer(self.opportunity_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class OpportunityCommentView(APIView):
    model = Comment
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Opportunities"],
        manual_parameters=swagger_params.opportunity_comment_edit_params,
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
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(
        tags=["Opportunities"],
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
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class OpportunityAttachmentView(APIView):
    model = Attachments
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Opportunities"],
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
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
