import json

from django.db.models import Q
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account, Tags
from accounts.serializer import AccountSerializer, TagsSerailizer
from common.models import Attachments, Comment, Profile

#from common.external_auth import CustomDualAuthentication
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    ProfileSerializer,
)
from common.utils import CURRENCY_CODES, SOURCES, STAGES
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from opportunity import swagger_params1
from opportunity.models import Opportunity
from opportunity.serializer import *
from opportunity.tasks import send_email_to_assigned_user
from teams.models import Teams


class OpportunityListView(APIView, LimitOffsetPagination):

    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Opportunity

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        accounts = Account.objects.filter(org=self.request.profile.org)
        contacts = Contact.objects.filter(org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()
            accounts = accounts.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))
            if params.get("account"):
                queryset = queryset.filter(account=params.get("account"))
            if params.get("stage"):
                queryset = queryset.filter(stage__contains=params.get("stage"))
            if params.get("lead_source"):
                queryset = queryset.filter(
                    lead_source__contains=params.get("lead_source")
                )
            if params.get("tags"):
                queryset = queryset.filter(
                    tags__in=params.get("tags")
                ).distinct()

        context = {}
        results_opportunities = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        opportunities = OpportunitySerializer(results_opportunities, many=True).data
        if results_opportunities:
            offset = queryset.filter(id__gte=results_opportunities[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update(
            {
                "opportunities_count": self.count,
                "offset": offset,
            }
        )
        context["opportunities"] = opportunities
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        context["tags"] = TagsSerailizer(Tags.objects.filter(), many=True).data
        context["stage"] = STAGES
        context["lead_source"] = SOURCES
        context["currency"] = CURRENCY_CODES

        return context

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.opportunity_list_get_params,
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,request=OpportunityCreateSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        serializer = OpportunityCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            opportunity_obj = serializer.save(
                created_by=request.profile.user,
                closed_on=params.get("due_date"),
                org=request.profile.org,
            )

            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                opportunity_obj.contacts.add(*contacts)

            if params.get("tags"):
                tags = params.get("tags")
                for tag in tags:
                    obj_tag = Tags.objects.filter(slug=tag.lower())
                    if obj_tag.exists():
                        obj_tag = obj_tag[0]
                    else:
                        obj_tag = Tags.objects.create(name=tag)
                    opportunity_obj.tags.add(obj_tag)

            if params.get("stage"):
                stage = params.get("stage")
                if stage in ["CLOSED WON", "CLOSED LOST"]:
                    opportunity_obj.closed_by = self.request.profile

            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                opportunity_obj.teams.add(*teams)

            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                opportunity_obj.assigned_to.add(*profiles)

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get(
                    "opportunity_attachment"
                ).name
                attachment.opportunity = opportunity_obj
                attachment.attachment = self.request.FILES.get("opportunity_attachment")
                attachment.save()

            recipients = list(
                opportunity_obj.assigned_to.all().values_list("id", flat=True)
            )

            send_email_to_assigned_user.delay(
                recipients,
                opportunity_obj.id,
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
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Opportunity

    def get_object(self, pk):
        return self.model.objects.filter(id=pk).first()

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,request=OpportunityCreateSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        params = request.data
        opportunity_object = self.get_object(pk=pk)
        if opportunity_object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == opportunity_object.created_by)
                or (self.request.profile in opportunity_object.assigned_to.all())
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
            # opportunity=True,
        )

        if serializer.is_valid():
            opportunity_object = serializer.save(closed_on=params.get("due_date"))
            previous_assigned_to_users = list(
                opportunity_object.assigned_to.all().values_list("id", flat=True)
            )
            opportunity_object.contacts.clear()
            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                opportunity_object.contacts.add(*contacts)

            opportunity_object.tags.clear()
            if params.get("tags"):
                tags = params.get("tags")
                for tag in tags:
                    obj_tag = Tags.objects.filter(slug=tag.lower())
                    if obj_tag.exists():
                        obj_tag = obj_tag[0]
                    else:
                        obj_tag = Tags.objects.create(name=tag)
                    opportunity_object.tags.add(obj_tag)

            if params.get("stage"):
                stage = params.get("stage")
                if stage in ["CLOSED WON", "CLOSED LOST"]:
                    opportunity_object.closed_by = self.request.profile

            opportunity_object.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                opportunity_object.teams.add(*teams)

            opportunity_object.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                opportunity_object.assigned_to.add(*profiles)

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
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
            )
            return Response(
                {"error": False, "message": "Opportunity Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Opportunities"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.profile != self.object.created_by:
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

    @extend_schema(
        tags=["Opportunities"], parameters=swagger_params1.organization_params
    )
    def get(self, request, pk, format=None):
        self.opportunity = self.get_object(pk=pk)
        context = {}
        context["opportunity_obj"] = OpportunitySerializer(self.opportunity).data
        if self.opportunity.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == self.opportunity.created_by)
                or (self.request.profile in self.opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comment_permission = False

        if (
            self.request.profile == self.opportunity.created_by
            or self.request.user.is_superuser
            or self.request.profile.role == "ADMIN"
        ):
            comment_permission = True

        if self.request.user.is_superuser or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
                    "user__email"
                )
            )
        elif self.request.profile != self.opportunity.created_by:
            if self.opportunity.created_by:
                users_mention = [
                    {"username": self.opportunity.created_by.user.email}
                ]
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
                "users": ProfileSerializer(
                    Profile.objects.filter(
                        is_active=True, org=self.request.profile.org
                    ).order_by("user__email"),
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

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,request=OpportunityDetailEditSwaggerSerializer
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        context = {}
        self.opportunity_obj = Opportunity.objects.get(pk=pk)
        if self.opportunity_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment_serializer = CommentSerializer(data=params)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == self.opportunity_obj.created_by)
                or (self.request.profile in self.opportunity_obj.assigned_to.all())
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
                    commented_by_id=self.request.profile.id,
                )

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
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
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,request=OpportunityCommentEditSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == obj.commented_by
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
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Opportunities"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
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
                "errors": "You do not have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class OpportunityAttachmentView(APIView):
    model = Attachments
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Opportunities"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
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
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
