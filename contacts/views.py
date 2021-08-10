from rest_framework import status
from common.models import User, Attachments, Comment
from contacts.models import Contact
from teams.models import Teams
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from common.custom_auth import JSONWebTokenAuthentication
from contacts import swagger_params
from contacts.serializer import *
from rest_framework.views import APIView
from common.utils import COUNTRIES
from common.serializer import (
    UserSerializer,
    CommentSerializer,
    AttachmentsSerializer,
    BillingAddressSerializer,
)
from teams.serializer import TeamsSerializer
from tasks.serializer import TaskSerializer
from django.contrib.sites.shortcuts import get_current_site
from contacts.tasks import send_email_to_assigned_user
import json
from django.conf import settings


class ContactsListView(APIView, LimitOffsetPagination):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Contact

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.all().order_by("-created_on")
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user)
            ).distinct()

        request_post = params
        if request_post:
            if request_post.get("name"):
                queryset = queryset.filter(
                    first_name__icontains=request_post.get("name")
                )
            if request_post.get("city"):
                queryset = queryset.filter(
                    address__city__icontains=request_post.get("city")
                )
            if request_post.get("phone"):
                queryset = queryset.filter(phone__icontains=request_post.get("phone"))
            if request_post.get("email"):
                queryset = queryset.filter(email__icontains=request_post.get("email"))
            if request_post.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=json.loads(request_post.get("assigned_to"))
                ).distinct()

        context = {}
        search = False
        if (
            params.get("first_name")
            or params.get("city")
            or params.get("phone")
            or params.get("email")
            or params.get("assigned_to")
        ):
            search = True
        context["search"] = search

        results_contact = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        contacts = ContactSerializer(results_contact, many=True).data
        context["per_page"] = 10
        context.update(
            {
                "contacts_count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_number": int(self.offset / 10) + 1,
            }
        )
        context["contact_obj_list"] = contacts
        context["users"] = UserSerializer(
            User.objects.filter(is_active=True).order_by("email"),
            many=True,
        ).data
        context["countries"] = COUNTRIES
        context["teams"] = TeamsSerializer(Teams.objects.all(), many=True).data
        context["per_page"] = params.get("per_page")
        context["assignedto_list"] = UserSerializer(User.objects.all(), many=True).data
        return context

    @swagger_auto_schema(
        tags=["contacts"], manual_parameters=swagger_params.contact_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["contacts"], manual_parameters=swagger_params.contact_create_post_params
    )
    def post(self, request, *args, **kwargs):
        params = request.query_params if len(request.data) == 0 else request.data
        contact_serializer = CreateContactSerializer(
            data=params, request_obj=request, contact=True
        )
        address_serializer = BillingAddressSerializer(data=params)

        data = {}
        if not contact_serializer.is_valid():
            data["contact_errors"] = contact_serializer.errors
        if not address_serializer.is_valid():
            data["address_errors"] = (address_serializer.errors,)
        if data:
            return Response(
                {"error": True, "errors": data},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # if contact_serializer.is_valid() and address_serializer.is_valid():
        address_obj = address_serializer.save()
        contact_obj = contact_serializer.save()
        contact_obj.address = address_obj
        contact_obj.created_by = self.request.user
        contact_obj.save()

        if self.request.user.role == "ADMIN":
            if params.get("teams"):
                teams = json.loads(params.get("teams"))
                for team in teams:
                    teams_ids = Teams.objects.filter(id=team)
                    if teams_ids.exists():
                        contact_obj.teams.add(team)
                    else:
                        contact_obj.delete()
                        data["team"] = "Please enter valid Team"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                assinged_to_users_ids = json.loads(params.get("assigned_to"))
                for user_id in assinged_to_users_ids:
                    user = User.objects.filter(id=user_id)
                    if user.exists():
                        contact_obj.assigned_to.add(user_id)
                    else:
                        contact_obj.delete()
                        data["assigned_to"] = "Please enter valid user"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

        assigned_to_list = list(
            contact_obj.assigned_to.all().values_list("id", flat=True)
        )
        recipients = assigned_to_list
        send_email_to_assigned_user.delay(
            recipients,
            contact_obj.id,
            domain=settings.Domain,
            protocol=self.request.scheme,
        )

        if request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = request.user
            attachment.file_name = request.FILES.get("contact_attachment").name
            attachment.contact = contact_obj
            attachment.attachment = request.FILES.get("contact_attachment")
            attachment.save()
        return Response(
            {"error": False, "message": "Contact created Successfuly"},
            status=status.HTTP_200_OK,
        )


class ContactDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Contact

    def get_object(self, pk):
        return get_object_or_404(Contact, pk=pk)

    @swagger_auto_schema(
        tags=["contacts"], manual_parameters=swagger_params.contact_create_post_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        contact_obj = self.get_object(pk=pk)
        address_obj = contact_obj.address

        contact_serializer = CreateContactSerializer(
            data=params, instance=contact_obj, request_obj=request, contact=True
        )
        address_serializer = BillingAddressSerializer(data=params, instance=address_obj)
        data = {}
        if not contact_serializer.is_valid():
            data["contact_errors"] = contact_serializer.errors
        if not address_serializer.is_valid():
            data["address_errors"] = (address_serializer.errors,)
        if data:
            data["error"] = True
            return Response(
                data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if contact_serializer.is_valid():
            if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
                if not (
                    (self.request.user == contact_obj.created_by)
                    or (self.request.user in contact_obj.assigned_to.all())
                ):
                    return Response(
                        {
                            "error": True,
                            "errors": "You do not have Permission to perform this action",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            address_obj = address_serializer.save()
            contact_obj = contact_serializer.save()
            contact_obj.address = address_obj
            contact_obj.save()
            contact_obj = contact_serializer.save()
            if self.request.user.role == "ADMIN":
                contact_obj.teams.clear()
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team)
                        if teams_ids.exists():
                            contact_obj.teams.add(team)
                        else:
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                contact_obj.assigned_to.clear()
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id)
                        if user.exists():
                            contact_obj.assigned_to.add(user_id)
                        else:
                            data["assigned_to"] = "Please enter valid user"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

            previous_assigned_to_users = list(
                contact_obj.assigned_to.all().values_list("id", flat=True)
            )

            assigned_to_list = list(
                contact_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                contact_obj.id,
                domain=settings.Domain,
                protocol=request.scheme,
            )
            if request.FILES.get("contact_attachment"):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get("contact_attachment").name
                attachment.contact = contact_obj
                attachment.attachment = request.FILES.get("contact_attachment")
                attachment.save()
            return Response(
                {"error": False, "message": "Contact Updated Successfully"},
                status=status.HTTP_200_OK,
            )

    @swagger_auto_schema(
        tags=["contacts"],
    )
    def get(self, request, pk, format=None):
        context = {}
        contact_obj = self.get_object(pk)
        context["contact_obj"] = ContactSerializer(contact_obj).data
        user_assgn_list = [
            assigned_to.id for assigned_to in contact_obj.assigned_to.all()
        ]
        user_assigned_accounts = set(
            self.request.user.account_assigned_users.values_list("id", flat=True)
        )
        contact_accounts = set(
            contact_obj.account_contacts.values_list("id", flat=True)
        )
        if user_assigned_accounts.intersection(contact_accounts):
            user_assgn_list.append(self.request.user.id)
        if self.request.user == contact_obj.created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        assigned_data = []
        for each in contact_obj.assigned_to.all():
            assigned_dict = {}
            assigned_dict["id"] = each.id
            assigned_dict["name"] = each.email
            assigned_data.append(assigned_dict)

        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            users_mention = list(User.objects.filter(is_active=True).values("username"))
        elif self.request.user != contact_obj.created_by:
            users_mention = [{"username": contact_obj.created_by.username}]
        else:
            users_mention = list(contact_obj.assigned_to.all().values("username"))

        if request.user == contact_obj.created_by:
            user_assgn_list.append(self.request.user.id)

        context["address_obj"] = BillingAddressSerializer(contact_obj.address).data
        context["users"] = UserSerializer(
            User.objects.filter(is_active=True).order_by("email"),
            many=True,
        ).data
        context["countries"] = COUNTRIES
        context["teams"] = TeamsSerializer(Teams.objects.all(), many=True).data
        context.update(
            {
                "comments": CommentSerializer(
                    contact_obj.contact_comments.all(), many=True
                ).data,
                "attachments": AttachmentsSerializer(
                    contact_obj.contact_attachment.all(), many=True
                ).data,
                "assigned_data": assigned_data,
                "tasks": TaskSerializer(
                    contact_obj.contacts_tasks.all(), many=True
                ).data,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @swagger_auto_schema(
        tags=["contacts"],
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            self.request.user.role != "ADMIN"
            and not self.request.user.is_superuser
            and self.request.user != self.object.created_by
        ):
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            if self.object.address_id:
                self.object.address.delete()
            self.object.delete()
        return Response(
            {"error": False, "message": "Contact Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["contacts"], manual_parameters=swagger_params.contact_detail_get_params
    )
    def post(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        context = {}
        self.contact_obj = Contact.objects.get(pk=pk)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.contact_obj.created_by)
                or (self.request.user in self.contact_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        comment_serializer = CommentSerializer(data=params)
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    contact_id=self.contact_obj.id,
                    commented_by_id=self.request.user.id,
                )

        if self.request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get("contact_attachment").name
            attachment.contact = self.contact_obj
            attachment.attachment = self.request.FILES.get("contact_attachment")
            attachment.save()

        comments = Comment.objects.filter(contact__id=self.contact_obj.id).order_by(
            "-id"
        )
        attachments = Attachments.objects.filter(
            contact__id=self.contact_obj.id
        ).order_by("-id")
        context.update(
            {
                "contact_obj": ContactSerializer(self.contact_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class ContactCommentView(APIView):
    model = Comment
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["contacts"], manual_parameters=swagger_params.contact_comment_edit_params
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
                    "errors": "You don't have permission to edit this Comment",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(tags=["contacts"])
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
                    "errors": "You don't have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class ContactAttachmentView(APIView):
    model = Attachments
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["contacts"])
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
                    "errors": "You don't have permission to delete this Attachment",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
