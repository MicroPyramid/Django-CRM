from common.models import User
from contacts.models import Contact
from teams.models import Teams
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from common.custom_auth import JSONWebTokenAuthentication
from contacts import swagger_params
from contacts.serializer import *
from rest_framework.views import APIView
from common.utils import COUNTRIES
from common.serializer import (UserSerializer, CommentSerializer,
                               AttachmentsSerializer, BillingAddressSerializer)
from teams.serializer import TeamsSerializer
from tasks.serializer import TaskSerializer
from django.contrib.sites.shortcuts import get_current_site
from contacts.tasks import send_email_to_assigned_user


class ContactsListView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Contact

    def get_queryset(self, params):
        queryset = self.model.objects.filter(
            company=self.request.company).order_by("-created_on")
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) | Q(
                    created_by=self.request.user)
            )

        request_post = params
        if request_post and params.get('is_filter'):
            if request_post.get("first_name"):
                queryset = queryset.filter(
                    first_name__icontains=request_post.get("first_name")
                )
            if request_post.get("city"):
                queryset = queryset.filter(
                    address__city__icontains=request_post.get("city")
                )
            if request_post.get("phone"):
                queryset = queryset.filter(
                    phone__icontains=request_post.get("phone"))
            if request_post.get("email"):
                queryset = queryset.filter(
                    email__icontains=request_post.get("email"))
            if request_post.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=request_post.getlist("assigned_to")
                )
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        params = self.request.query_params if len(
            self.request.data) == 0 else self.request.data
        context = {}
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            self.users = User.objects.filter(
                is_active=True, company=self.request.company).order_by("email")
        else:
            self.users = User.objects.filter(
                role="ADMIN", company=self.request.company).order_by("email")
        context["users"] = UserSerializer(self.users, many=True).data
        context["countries"] = COUNTRIES
        context["assignedto_list"] = [
            int(i) for i in params.getlist("assigned_to", []) if i
        ]
        context["teams"] = TeamsSerializer(Teams.objects.filter(
            company=self.request.company), many=True).data
        context["contact_obj_list"] = ContactSerializer(
            self.get_queryset(params), many=True).data
        context["per_page"] = params.get("per_page")
        context["users"] = UserSerializer(
            User.objects.filter(is_active=True).order_by("username"), many=True).data
        context["assignedto_list"] = [
            int(i) for i in params.getlist("assigned_to", []) if i
        ]
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
        return context

    @swagger_auto_schema(tags=["contacts"], manual_parameters=swagger_params.contact_list_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(tags=["contacts"], manual_parameters=swagger_params.contact_create_post_params)
    def post(self, request, *args, **kwargs):
        params = request.query_params if len(
            request.data) == 0 else request.data
        contact_serializer = CreateContctForm(data=params)
        address_serializer = BillingAddressSerializer(data=params)
        data = {}
        if not contact_serializer.is_valid():
            data['contact_errors'] = contact_serializer.errors
        if not address_serializer.is_valid():
            data["address_errors"] = address_serializer.errors,
        if data:
            data['error'] = True
            return Response(data)
        address_obj = address_serializer.save()
        contact_obj = contact_serializer.save()
        contact_obj.address = address_obj
        contact_obj.created_by = self.request.user
        contact_obj.company = self.request.company
        contact_obj.save()
        if self.request.GET.get("view_account", None):
            if Account.objects.filter(
                id=int(self.request.GET.get("view_account"))
            ).exists():
                Account.objects.get(
                    id=int(self.request.GET.get("view_account"))
                ).contacts.add(contact_obj)
        if params.getlist("assigned_to", []):
            contact_obj.assigned_to.add(
                *params.getlist("assigned_to"))
        if params.getlist("teams", []):
            user_ids = Teams.objects.filter(
                id__in=params.getlist("teams")
            ).values_list("users", flat=True)
            assinged_to_users_ids = contact_obj.assigned_to.all().values_list(
                "id", flat=True
            )
            for user_id in user_ids:
                if user_id not in assinged_to_users_ids:
                    contact_obj.assigned_to.add(user_id)

        if params.getlist("teams", []):
            contact_obj.teams.add(*params.getlist("teams"))

        assigned_to_list = list(
            contact_obj.assigned_to.all().values_list("id", flat=True)
        )
        current_site = get_current_site(self.request)
        recipients = assigned_to_list
        send_email_to_assigned_user.delay(
            recipients,
            contact_obj.id,
            domain=current_site.domain,
            protocol=self.request.scheme,
        )

        if request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = request.user
            attachment.file_name = request.FILES.get(
                "contact_attachment").name
            attachment.contact = contact_obj
            attachment.attachment = request.FILES.get("contact_attachment")
            attachment.save()

        return Response({'error': False, 'message': 'Contact created Successfuly'})


class ContactDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Contact

    def get_object(self, pk):
        return get_object_or_404(Contact, pk=pk)

    @swagger_auto_schema(tags=["contacts"], manual_parameters=swagger_params.contact_create_post_params)
    def put(self, request, pk, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        self.object = self.get_object(pk)
        address_obj = self.object.address
        contact_serializer = CreateContctForm(
            data=params, instance=self.object)
        address_serializer = BillingAddressSerializer(
            data=params, instance=address_obj)
        data = {}
        if not contact_serializer.is_valid():
            data['contact_errors'] = contact_serializer.errors
        if not address_serializer.is_valid():
            data["address_errors"] = address_serializer.errors,
        if data:
            data['error'] = True
            return Response(data)
        addres_obj = address_serializer.save()
        contact_obj = contact_serializer.save()
        contact_obj.address = addres_obj
        contact_obj.save()

        previous_assigned_to_users = list(
            contact_obj.assigned_to.all().values_list("id", flat=True)
        )
        if params.getlist("assigned_to", []):
            current_site = get_current_site(request)

            contact_obj.assigned_to.clear()
            contact_obj.assigned_to.add(
                *params.getlist("assigned_to"))
        else:
            contact_obj.assigned_to.clear()

        if params.getlist("teams", []):
            user_ids = Teams.objects.filter(
                id__in=params.getlist("teams")
            ).values_list("users", flat=True)
            assinged_to_users_ids = contact_obj.assigned_to.all().values_list(
                "id", flat=True
            )
            for user_id in user_ids:
                if user_id not in assinged_to_users_ids:
                    contact_obj.assigned_to.add(user_id)

        if params.getlist("teams", []):
            contact_obj.teams.clear()
            contact_obj.teams.add(*params.getlist("teams"))
        else:
            contact_obj.teams.clear()

        current_site = get_current_site(request)
        assigned_to_list = list(
            contact_obj.assigned_to.all().values_list("id", flat=True)
        )
        recipients = list(set(assigned_to_list) -
                          set(previous_assigned_to_users))
        send_email_to_assigned_user.delay(
            recipients,
            contact_obj.id,
            domain=current_site.domain,
            protocol=request.scheme,
        )
        if request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = request.user
            attachment.file_name = request.FILES.get(
                "contact_attachment").name
            attachment.contact = contact_obj
            attachment.attachment = request.FILES.get(
                "contact_attachment")
            attachment.save()
        return Response({'error': False})

    @swagger_auto_schema(tags=["contacts"], manual_parameters=swagger_params.contact_detail_get_params)
    def get(self, request, pk, format=None):
        context = {}
        contact_obj = self.get_object(pk)
        context["contact_obj"] = ContactSerializer(contact_obj).data
        user_assgn_list = [
            assigned_to.id for assigned_to in contact_obj.assigned_to.all()
        ]
        user_assigned_accounts = set(
            self.request.user.account_assigned_users.values_list(
                "id", flat=True)
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
                raise PermissionDenied
        assigned_data = []
        for each in contact_obj.assigned_to.all():
            assigned_dict = {}
            assigned_dict["id"] = each.id
            assigned_dict["name"] = each.email
            assigned_data.append(assigned_dict)

        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            users_mention = list(
                User.objects.filter(
                    is_active=True, company=self.request.company
                ).values("username")
            )
        elif self.request.user != contact_obj.created_by:
            users_mention = [
                {"username": contact_obj.created_by.username}]
        else:
            users_mention = list(
                contact_obj.assigned_to.all().values("username"))

        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            self.users = User.objects.filter(
                is_active=True, company=self.request.company).order_by("email")
        else:
            self.users = User.objects.filter(
                role="ADMIN", company=self.request.company).order_by("email")
        if request.user == contact_obj.created_by:
            user_assgn_list.append(self.request.user.id)

        context["address_obj"] = BillingAddressSerializer(
            contact_obj.address).data
        context["users"] = UserSerializer(self.users, many=True).data
        context["countries"] = COUNTRIES
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(company=request.company), many=True).data
        context.update(
            {
                "comments": CommentSerializer(
                    contact_obj.contact_comments.all(), many=True).data,
                "attachments": AttachmentsSerializer(
                    contact_obj.contact_attachment.all(), many=True).data,
                "assigned_data": assigned_data,
                "tasks": TaskSerializer(
                    contact_obj.contacts_tasks.all(), many=True).data,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @swagger_auto_schema(tags=["contacts"], manual_parameters=swagger_params.contact_delete_get_params)
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            self.request.user.role != "ADMIN"
            and not self.request.user.is_superuser
            and self.request.user != self.object.created_by
        ) or self.object.company != self.request.company:
            raise PermissionDenied
        else:
            if self.object.address_id:
                self.object.address.delete()
            self.object.delete()
        return Response({"error": False})
