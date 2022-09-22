from django.db.models import Q

from cases.models import Case
from cases.tasks import send_email_to_assigned_user
from cases import swagger_params
from cases.serializer import (
    CaseSerializer,
    CaseCreateSerializer,
)
from accounts.models import Account
from accounts.serializer import AccountSerializer
from common.models import Attachments, Comment, Profile

# from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import (
    CommentSerializer,
    AttachmentsSerializer,
)
from common.utils import (
    STATUS_CHOICE,
    PRIORITY_CHOICE,
    CASE_TYPE,
)
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from teams.models import Teams

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from drf_yasg.utils import swagger_auto_schema
import json


class CaseListView(APIView, LimitOffsetPagination):

    # authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Case

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(org=self.request.org).order_by("-id")
        accounts = Account.objects.filter(org=self.request.org).order_by("-id")
        contacts = Contact.objects.filter(org=self.request.org).order_by("-id")
        profiles = Profile.objects.filter(is_active=True, org=self.request.org)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(created_by=self.request.profile) | Q(assigned_to=self.request.profile)
            ).distinct()
            accounts = accounts.filter(
                Q(created_by=self.request.profile) | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile) | Q(assigned_to=self.request.profile)
            ).distinct()
            profiles = profiles.filter(role="ADMIN")

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            if params.get("priority"):
                queryset = queryset.filter(priority=params.get("priority"))
            if params.get("account"):
                queryset = queryset.filter(account=params.get("account"))

        context = {}

        results_cases = self.paginate_queryset(queryset, self.request, view=self)
        cases = CaseSerializer(results_cases, many=True).data

        if results_cases:
            offset = queryset.filter(id__gte=results_cases[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context.update(
            {
                "cases_count": self.count,
                "offset": offset,
            }
        )
        context["cases"] = cases
        context["status"] = STATUS_CHOICE
        context["priority"] = PRIORITY_CHOICE
        context["type_of_case"] = CASE_TYPE
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        return context

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.cases_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.cases_create_post_params
    )
    def post(self, request, *args, **kwargs):
        params = request.query_params if len(request.data) == 0 else request.data
        serializer = CaseCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            cases_obj = serializer.save(
                created_by=request.profile,
                org=request.org,
                closed_on=params.get("closed_on"),
                case_type=params.get("type_of_case"),
            )

            if params.get("contacts"):
                contacts_list = json.loads(params.get("contacts"))
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.org)
                if contacts:
                    cases_obj.contacts.add(*contacts)

            if params.get("teams"):
                teams_list = json.loads(params.get("teams"))
                teams = Teams.objects.filter(id__in=teams_list, org=request.org)
                if teams.exists():
                    cases_obj.teams.add(*teams)

            if params.get("assigned_to"):
                assinged_to_list = json.loads(params.get("assigned_to"))
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.org, is_active=True
                )
                if profiles:
                    cases_obj.assigned_to.add(*profiles)

            if self.request.FILES.get("case_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile
                attachment.file_name = self.request.FILES.get("case_attachment").name
                attachment.cases = cases_obj
                attachment.attachment = self.request.FILES.get("case_attachment")
                attachment.save()

            recipients = list(cases_obj.assigned_to.all().values_list("id", flat=True))
            send_email_to_assigned_user.delay(
                recipients,
                cases_obj.id,
            )
            return Response(
                {"error": False, "message": "Case Created Successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CaseDetailView(APIView):
    # authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Case

    def get_object(self, pk):
        return self.model.objects.filter(id=pk).first()

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.cases_create_post_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        cases_object = self.get_object(pk=pk)
        if cases_object.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == cases_object.created_by)
                or (self.request.profile in cases_object.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = CaseCreateSerializer(
            cases_object,
            data=params,
            request_obj=request,
        )

        if serializer.is_valid():
            cases_object = serializer.save(
                closed_on=params.get("closed_on"), case_type=params.get("type_of_case")
            )
            previous_assigned_to_users = list(
                cases_object.assigned_to.all().values_list("id", flat=True)
            )
            cases_object.contacts.clear()
            if params.get("contacts"):
                contacts_list = json.loads(params.get("contacts"))
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.org)
                if contacts:
                    cases_object.contacts.add(*contacts)

            cases_object.teams.clear()
            if params.get("teams"):
                teams_list = json.loads(params.get("teams"))
                teams = Teams.objects.filter(id__in=teams_list, org=request.org)
                if teams.exists():
                    cases_object.teams.add(*teams)

            cases_object.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = json.loads(params.get("assigned_to"))
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.org, is_active=True
                )
                if profiles:
                    cases_object.assigned_to.add(*profiles)

            if self.request.FILES.get("case_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile
                attachment.file_name = self.request.FILES.get("case_attachment").name
                attachment.case = cases_object
                attachment.attachment = self.request.FILES.get("case_attachment")
                attachment.save()

            assigned_to_list = list(
                cases_object.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                cases_object.id,
            )
            return Response(
                {"error": False, "message": "Case Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
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
            {"error": False, "message": "Case Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, pk, format=None):
        self.cases = self.get_object(pk=pk)
        if self.cases.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        context["cases_obj"] = CaseSerializer(self.cases).data
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.cases.created_by)
                or (self.request.profile in self.cases.assigned_to.all())
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
            self.request.profile == self.cases.created_by
            or self.request.profile.is_admin
            or self.request.profile.role == "ADMIN"
        ):
            comment_permission = True

        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(is_active=True, org=self.request.org).values(
                    "user__username"
                )
            )
        elif self.request.profile != self.cases.created_by:
            if self.cases.created_by:
                users_mention = [{"username": self.cases.created_by.user.username}]
            else:
                users_mention = []
        else:
            users_mention = []

        attachments = Attachments.objects.filter(case=self.cases).order_by("-id")
        comments = Comment.objects.filter(case=self.cases).order_by("-id")

        context.update(
            {
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "contacts": ContactSerializer(
                    self.cases.contacts.all(), many=True
                ).data,
                "status": STATUS_CHOICE,
                "priority": PRIORITY_CHOICE,
                "type_of_case": CASE_TYPE,
                "comment_permission": comment_permission,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.cases_detail_get_params
    )
    def post(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        self.cases_obj = Case.objects.get(pk=pk)
        if self.cases_obj.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        comment_serializer = CommentSerializer(data=params)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.cases_obj.created_by)
                or (self.request.profile in self.cases_obj.assigned_to.all())
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
                    case_id=self.cases_obj.id,
                    commented_by_id=self.request.profile.id,
                )

        if self.request.FILES.get("case_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile
            attachment.file_name = self.request.FILES.get("case_attachment").name
            attachment.case = self.cases_obj
            attachment.attachment = self.request.FILES.get("case_attachment")
            attachment.save()

        attachments = Attachments.objects.filter(case=self.cases_obj).order_by("-id")
        comments = Comment.objects.filter(case=self.cases_obj).order_by("-id")

        context.update(
            {
                "cases_obj": CaseSerializer(self.cases_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class CaseCommentView(APIView):
    model = Comment
    # authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.cases_comment_edit_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
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

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.organization_params
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
                "errors": "You do not have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class CaseAttachmentView(APIView):
    model = Attachments
    # authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Cases"], manual_parameters=swagger_params.organization_params
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
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
