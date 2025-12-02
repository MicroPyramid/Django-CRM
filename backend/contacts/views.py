import json

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import HasOrgContext
from rest_framework.views import APIView

from common.models import Attachments, Comment, Profile, Tags, Teams
from common.serializer import AttachmentsSerializer, CommentSerializer
from common.utils import COUNTRIES
from contacts import swagger_params
from contacts.models import Contact, Profile
from contacts.serializer import *
from contacts.tasks import send_email_to_assigned_user
from tasks.serializer import TaskSerializer


class ContactsListView(APIView, LimitOffsetPagination):
    permission_classes = (IsAuthenticated, HasOrgContext)
    model = Contact

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by(
            "-id"
        )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile])
                | Q(created_by=self.request.profile.user)
            ).distinct()

        if params:
            if params.get("name"):
                queryset = queryset.filter(first_name__icontains=params.get("name"))
            if params.get("city"):
                queryset = queryset.filter(address__city__icontains=params.get("city"))
            if params.get("phone"):
                queryset = queryset.filter(phone__icontains=params.get("phone"))
            if params.get("email"):
                queryset = queryset.filter(email__icontains=params.get("email"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.get("assigned_to")
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
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        # Standard DRF pagination format for frontend compatibility
        context["count"] = self.count
        context["results"] = contacts
        # Legacy format for backwards compatibility
        context["contacts_count"] = self.count
        context["offset"] = offset
        context["contact_obj_list"] = contacts
        context["countries"] = COUNTRIES
        users = Profile.objects.filter(
            is_active=True, org=self.request.profile.org
        ).values("id", "user__email")
        context["users"] = users

        return context

    @extend_schema(tags=["contacts"], parameters=swagger_params.contact_list_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params.organization_params,
        request=CreateContactSerializer,
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        contact_serializer = CreateContactSerializer(data=params, request_obj=request)

        if not contact_serializer.is_valid():
            return Response(
                {"error": True, "errors": contact_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Contact model uses flat address fields, no separate Address object needed
        contact_obj = contact_serializer.save(org=request.profile.org)

        if params.get("teams"):
            teams_list = params.get("teams")
            teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
            contact_obj.teams.add(*teams)

        if params.get("assigned_to"):
            assinged_to_list = params.get("assigned_to")
            profiles = Profile.objects.filter(
                id__in=assinged_to_list, org=request.profile.org
            )
            contact_obj.assigned_to.add(*profiles)

        if params.get("tags"):
            tags = params.get("tags")
            if isinstance(tags, str):
                tags = json.loads(tags)
            for tag in tags:
                tag_obj = Tags.objects.filter(slug=tag.lower(), org=request.profile.org)
                if tag_obj.exists():
                    tag_obj = tag_obj[0]
                else:
                    tag_obj = Tags.objects.create(name=tag, org=request.profile.org)
                contact_obj.tags.add(tag_obj)

        recipients = list(contact_obj.assigned_to.all().values_list("id", flat=True))
        send_email_to_assigned_user.delay(
            recipients,
            contact_obj.id,
        )

        if request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = request.profile.user
            attachment.file_name = request.FILES.get("contact_attachment").name
            attachment.content_object = contact_obj
            attachment.attachment = request.FILES.get("contact_attachment")
            attachment.org = request.profile.org
            attachment.save()
        return Response(
            {"error": False, "message": "Contact created Successfuly"},
            status=status.HTTP_200_OK,
        )


class ContactDetailView(APIView):
    # #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated, HasOrgContext)
    model = Contact

    def get_object(self, pk):
        return get_object_or_404(Contact, pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params.contact_create_post_params,
        request=CreateContactSerializer,
    )
    def put(self, request, pk, format=None):
        data = request.data
        contact_obj = self.get_object(pk=pk)
        if contact_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        contact_serializer = CreateContactSerializer(
            data=data, instance=contact_obj, request_obj=request
        )
        if not contact_serializer.is_valid():
            return Response(
                {"error": True, "errors": contact_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        contact_obj = contact_serializer.save()
        contact_obj.teams.clear()
        if data.get("teams"):
            teams_list = json.loads(data.get("teams"))
            teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
            contact_obj.teams.add(*teams)

        contact_obj.assigned_to.clear()
        if data.get("assigned_to"):
            assinged_to_list = json.loads(data.get("assigned_to"))
            profiles = Profile.objects.filter(
                id__in=assinged_to_list, org=request.profile.org
            )
            contact_obj.assigned_to.add(*profiles)

        contact_obj.tags.clear()
        if data.get("tags"):
            tags = data.get("tags")
            if isinstance(tags, str):
                tags = json.loads(tags)
            for tag in tags:
                tag_obj = Tags.objects.filter(slug=tag.lower(), org=request.profile.org)
                if tag_obj.exists():
                    tag_obj = tag_obj[0]
                else:
                    tag_obj = Tags.objects.create(name=tag, org=request.profile.org)
                contact_obj.tags.add(tag_obj)

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
        )
        if request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = request.profile.user
            attachment.file_name = request.FILES.get("contact_attachment").name
            attachment.content_object = contact_obj
            attachment.attachment = request.FILES.get("contact_attachment")
            attachment.org = request.profile.org
            attachment.save()
        return Response(
            {"error": False, "message": "Contact Updated Successfully"},
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=["contacts"], parameters=swagger_params.organization_params)
    def get(self, request, pk, format=None):
        context = {}
        contact_obj = self.get_object(pk)
        context["contact_obj"] = ContactSerializer(contact_obj).data
        user_assgn_list = [
            assigned_to.id for assigned_to in contact_obj.assigned_to.all()
        ]
        user_assigned_accounts = set(
            self.request.profile.account_assigned_users.values_list("id", flat=True)
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
            assigned_dict["id"] = each.user.id
            assigned_dict["name"] = each.user.email
            assigned_data.append(assigned_dict)

        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(is_active=True, org=request.profile.org).values(
                    "user__email"
                )
            )
        elif self.request.profile != contact_obj.created_by:
            users_mention = [{"username": contact_obj.created_by.user.email}]
        else:
            users_mention = list(contact_obj.assigned_to.all().values("user__email"))

        if request.profile == contact_obj.created_by:
            user_assgn_list.append(self.request.profile.id)

        # Address is now flat fields on Contact model
        context["address_obj"] = {
            "address_line": contact_obj.address_line,
            "city": contact_obj.city,
            "state": contact_obj.state,
            "postcode": contact_obj.postcode,
            "country": contact_obj.country,
        }
        context["countries"] = COUNTRIES
        contact_content_type = ContentType.objects.get_for_model(Contact)
        comments = Comment.objects.filter(
            content_type=contact_content_type,
            object_id=contact_obj.id,
            org=request.profile.org,
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=contact_content_type,
            object_id=contact_obj.id,
            org=request.profile.org,
        ).order_by("-id")
        context.update(
            {
                "comments": CommentSerializer(comments, many=True).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "assigned_data": assigned_data,
                "tasks": TaskSerializer(
                    contact_obj.contacts_tasks.all(), many=True
                ).data,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @extend_schema(tags=["contacts"], parameters=swagger_params.organization_params)
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if (
            self.request.profile.role != "ADMIN"
            and not self.request.profile.is_admin
            and self.request.profile.user != self.object.created_by
        ):
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.object.delete()
        return Response(
            {"error": False, "message": "Contact Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params.organization_params,
        request=ContactDetailEditSwaggerSerializer,
    )
    def post(self, request, pk, **kwargs):
        params = request.data
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
                    org=request.profile.org,
                )

        if self.request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile.user
            attachment.file_name = self.request.FILES.get("contact_attachment").name
            attachment.content_object = self.contact_obj
            attachment.attachment = self.request.FILES.get("contact_attachment")
            attachment.org = self.request.profile.org
            attachment.save()

        contact_content_type = ContentType.objects.get_for_model(Contact)
        comments = Comment.objects.filter(
            content_type=contact_content_type,
            object_id=self.contact_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=contact_content_type,
            object_id=self.contact_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        context.update(
            {
                "contact_obj": ContactSerializer(self.contact_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params.organization_params,
        request=CreateContactSerializer,
        description="Partial Contact Update",
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to a contact."""
        data = request.data
        contact_obj = self.get_object(pk=pk)
        if contact_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company does not match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
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

        contact_serializer = CreateContactSerializer(
            data=data, instance=contact_obj, request_obj=request, partial=True
        )
        if not contact_serializer.is_valid():
            return Response(
                {"error": True, "errors": contact_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contact_obj = contact_serializer.save()

        # Handle M2M fields if present in request
        if "teams" in data:
            contact_obj.teams.clear()
            teams_list = data.get("teams")
            if teams_list:
                if isinstance(teams_list, str):
                    teams_list = json.loads(teams_list)
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                contact_obj.teams.add(*teams)

        if "assigned_to" in data:
            contact_obj.assigned_to.clear()
            assigned_to_list = data.get("assigned_to")
            if assigned_to_list:
                if isinstance(assigned_to_list, str):
                    assigned_to_list = json.loads(assigned_to_list)
                profiles = Profile.objects.filter(
                    id__in=assigned_to_list, org=request.profile.org
                )
                contact_obj.assigned_to.add(*profiles)

        if "tags" in data:
            contact_obj.tags.clear()
            tags_list = data.get("tags")
            if tags_list:
                if isinstance(tags_list, str):
                    tags_list = json.loads(tags_list)
                for tag in tags_list:
                    tag_obj = Tags.objects.filter(slug=tag.lower(), org=request.profile.org)
                    if tag_obj.exists():
                        tag_obj = tag_obj[0]
                    else:
                        tag_obj = Tags.objects.create(name=tag, org=request.profile.org)
                    contact_obj.tags.add(tag_obj)

        return Response(
            {"error": False, "message": "Contact Updated Successfully"},
            status=status.HTTP_200_OK,
        )


class ContactCommentView(APIView):
    model = Comment
    # #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params.organization_params,
        request=ContactCommentEditSwaggerSerializer,
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
                "errors": "You don't have permission to edit this Comment",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params.organization_params,
        request=ContactCommentEditSwaggerSerializer,
        description="Partial Comment Update",
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to a comment."""
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"error": False, "message": "Comment Updated"},
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

    @extend_schema(tags=["contacts"], parameters=swagger_params.organization_params)
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
    # #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["contacts"], parameters=swagger_params.organization_params)
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
