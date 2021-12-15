from rest_framework import status
from common.models import Attachments, Comment
from contacts.models import Contact, Profile
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
    CommentSerializer,
    AttachmentsSerializer,
    BillingAddressSerializer,
)
from tasks.serializer import TaskSerializer
from contacts.tasks import send_email_to_assigned_user
import json


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
        queryset = self.model.objects.filter(
            org=self.request.org).order_by("-id")
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile]) | Q(
                    created_by=self.request.profile)
            ).distinct()
        if params:
            if params.get("name"):
                queryset = queryset.filter(
                    first_name__icontains=params.get("name")
                )
            if params.get("city"):
                queryset = queryset.filter(
                    address__city__icontains=params.get("city")
                )
            if params.get("phone"):
                queryset = queryset.filter(
                    mobile_number__icontains=params.get("phone"))
            if params.get("email"):
                queryset = queryset.filter(
                    primary_email__icontains=params.get("email"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=json.loads(params.get("assigned_to"))
                ).distinct()

        context = {}
        results_contact = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        contacts = ContactSerializer(results_contact, many=True).data
        if results_contact:
            offset = queryset.filter(id__gte=results_contact[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context.update(
            {
                "contacts_count": self.count,
                "offset": offset
            }
        )
        context["contact_obj_list"] = contacts
        context["countries"] = COUNTRIES
        context["per_page"] = params.get("per_page")
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
        params = request.query_params if len(
            request.data) == 0 else request.data
        contact_serializer = CreateContactSerializer(
            data=params, request_obj=request
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
        contact_obj = contact_serializer.save(
            date_of_birth=params.get("date_of_birth")
        )
        contact_obj.address = address_obj
        contact_obj.created_by = self.request.profile
        contact_obj.org = request.org
        contact_obj.save()

        if params.get("teams"):
            teams_list = json.loads(params.get("teams"))
            teams = Teams.objects.filter(
                id__in=teams_list, org=request.org)
            contact_obj.teams.add(*teams)

        if params.get("assigned_to"):
            assinged_to_list = json.loads(
                params.get("assigned_to"))
            profiles = Profile.objects.filter(
                id__in=assinged_to_list, org=request.org)
            contact_obj.assigned_to.add(*profiles)

        recipients = list(
            contact_obj.assigned_to.all().values_list("id", flat=True)
        )
        send_email_to_assigned_user.delay(
            recipients,
            contact_obj.id,
        )

        if request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = request.profile
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
        params = request.query_params if len(
            request.data) == 0 else request.data
        contact_obj = self.get_object(pk=pk)
        address_obj = contact_obj.address
        if contact_obj.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN
            )
        contact_serializer = CreateContactSerializer(
            data=params, instance=contact_obj, request_obj=request, contact=True
        )
        address_serializer = BillingAddressSerializer(
            data=params, instance=address_obj)
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
            if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
                if not (
                    (self.request.profile == contact_obj.created_by)
                    or (self.request.profile in contact_obj.assigned_to.all())
                ):
                    return Response(
                        {
                            "error": True,
                            "errors": "You do not have Permission to perform this action",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            address_obj = address_serializer.save()
            contact_obj = contact_serializer.save(
                date_of_birth=params.get("date_of_birth")
            )
            contact_obj.address = address_obj
            contact_obj.save()
            contact_obj = contact_serializer.save()
            contact_obj.teams.clear()
            if params.get("teams"):
                teams_list = json.loads(params.get("teams"))
                teams = Teams.objects.filter(
                    id__in=teams_list, org=request.org)
                contact_obj.teams.add(*teams)

            contact_obj.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = json.loads(
                    params.get("assigned_to"))
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.org)
                contact_obj.assigned_to.add(*profiles)

            previous_assigned_to_users = list(
                contact_obj.assigned_to.all().values_list("id", flat=True)
            )

            assigned_to_list = list(
                contact_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) -
                              set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                contact_obj.id,
            )
            if request.FILES.get("contact_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile
                attachment.file_name = request.FILES.get(
                    "contact_attachment").name
                attachment.contact = contact_obj
                attachment.attachment = request.FILES.get("contact_attachment")
                attachment.save()
            return Response(
                {"error": False, "message": "Contact Updated Successfully"},
                status=status.HTTP_200_OK,
            )

    @swagger_auto_schema(
        tags=["contacts"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, pk, format=None):
        context = {}
        contact_obj = self.get_object(pk)
        context["contact_obj"] = ContactSerializer(contact_obj).data
        user_assgn_list = [
            assigned_to.id for assigned_to in contact_obj.assigned_to.all()
        ]
        user_assigned_accounts = set(
            self.request.profile.account_assigned_users.values_list(
                "id", flat=True)
        )
        contact_accounts = set(
            contact_obj.account_contacts.values_list("id", flat=True)
        )
        if user_assigned_accounts.intersection(contact_accounts):
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile == contact_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if self.request.profile.id not in user_assgn_list:
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

        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(Profile.objects.filter(
                is_active=True, org=request.org).values("user__username"))
        elif self.request.profile != contact_obj.created_by:
            users_mention = [
                {"username": contact_obj.created_by.user.username}]
        else:
            users_mention = list(
                contact_obj.assigned_to.all().values("username"))

        if request.profile == contact_obj.created_by:
            user_assgn_list.append(self.request.profile.id)

        context["address_obj"] = BillingAddressSerializer(
            contact_obj.address).data
        context["countries"] = COUNTRIES
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
        tags=["contacts"], manual_parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN
            )
        if (
            self.request.profile.role != "ADMIN"
            and not self.request.profile.is_admin
            and self.request.profile != self.object.created_by
        ):
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
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
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.contact_obj.created_by)
                or (self.request.profile in self.contact_obj.assigned_to.all())
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
                    commented_by_id=self.request.profile.id,
                    org=request.org
                )

        if self.request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile
            attachment.file_name = self.request.FILES.get(
                "contact_attachment").name
            attachment.contact = self.contact_obj
            attachment.attachment = self.request.FILES.get(
                "contact_attachment")
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
        params = request.query_params if len(
            request.data) == 0 else request.data
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
                "errors": "You don't have permission to edit this Comment",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @swagger_auto_schema(tags=["contacts"], manual_parameters=swagger_params.organization_params)
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
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class ContactAttachmentView(APIView):
    model = Attachments
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["contacts"], manual_parameters=swagger_params.organization_params)
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
                "errors": "You don't have permission to delete this Attachment",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
