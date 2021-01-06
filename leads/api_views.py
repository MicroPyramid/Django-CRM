from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from accounts.models import Account, Tags
from accounts.tasks import send_email_to_assigned_user
from leads import swagger_params
from accounts.serializer import (
    TagsSerailizer,
)
from common.models import User, Attachments, Comment
from common.utils import (
    COUNTRIES,
    LEAD_SOURCE,
    LEAD_STATUS
)
from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import (UserSerializer, CommentSerializer,
                               AttachmentsSerializer)
from leads.models import Lead
from leads.serializer import LeadSerializer, LeadCreateSerializer
from teams.serializer import TeamsSerializer
from teams.models import Teams
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema


class LeadListView(APIView):
    model = Lead
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = (
            self.model.objects.filter(company=self.request.company)
            .exclude(status="converted")
            .select_related("created_by")
            .prefetch_related(
                "tags",
                "assigned_to",
            )
        )
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) | Q(
                    created_by=self.request.user)
            )

        request_post = params
        if request_post and params.get('is_filter'):
            if request_post.get("name"):
                queryset = queryset.filter(
                    Q(first_name__icontains=request_post.get("name"))
                    & Q(last_name__icontains=request_post.get("name"))
                )
            if request_post.get("city"):
                queryset = queryset.filter(
                    city__icontains=request_post.get("city"))
            if request_post.get("email"):
                queryset = queryset.filter(
                    email__icontains=request_post.get("email"))
            if request_post.get("status"):
                queryset = queryset.filter(status=request_post.get("status"))
            if request_post.get("tag"):
                queryset = queryset.filter(
                    tags__in=request_post.getlist("tag"))
            if request_post.get("source"):
                queryset = queryset.filter(source=request_post.get("source"))
            if request_post.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=request_post.getlist("assigned_to")
                )
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = {}
        open_leads = self.get_queryset().exclude(status="closed")
        close_leads = self.get_queryset().filter(status="closed")
        context["status"] = LEAD_STATUS
        context["open_leads"] = LeadSerializer(open_leads, many=True).data
        context["close_leads"] = LeadSerializer(close_leads, many=True).data
        context["source"] = LEAD_SOURCE
        users = []
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            users = User.objects.filter(
                is_active=True,
                company=self.request.company).order_by("email")
        elif self.request.user.google.all():
            users = []
        else:
            users = User.objects.filter(
                role="ADMIN",
                company=self.request.company).order_by("email")
        context["users"] = UserSerializer(users, many=True).data
        tag_ids = list(
            set(
                self.get_queryset().values_list(
                    "tags",
                    flat=True,
                )
            )
        )
        context["tags"] = TagsSerailizer(
            Tags.objects.filter(id__in=tag_ids), many=True).data
        context["countries"] = COUNTRIES
        return context

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_create_post_params
    )
    def post(self, request, *args, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )

        serializer = LeadCreateSerializer(
            data=params, request_obj=request)
        if serializer.is_valid():
            lead_obj = serializer.save(
                created_by=request.user, company=request.company)
            if params.get("tags", ""):
                tags = params.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t)
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)
            if params.getlist("assigned_to", []):
                lead_obj.assigned_to.add(*params.getlist("assigned_to"))
                assigned_to_list = params.getlist("assigned_to")
            if params.getlist("teams", []):
                user_ids = Teams.objects.filter(
                    id__in=params.getlist("teams")
                ).values_list("users", flat=True)
                assinged_to_users_ids = lead_obj.assigned_to.all().values_list(
                    "id", flat=True
                )
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        lead_obj.assigned_to.add(user_id)

            if params.getlist("teams", []):
                lead_obj.teams.add(*params.getlist("teams"))

            current_site = get_current_site(request)
            recipients = list(
                lead_obj.assigned_to.all().values_list("id", flat=True))
            send_email_to_assigned_user.delay(
                recipients,
                lead_obj.id,
                domain=current_site.domain,
                protocol=request.scheme,
            )

            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    "lead_attachment").name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.save()

            if params.get("status") == "converted":
                account_object = Account.objects.create(
                    created_by=request.user,
                    name=lead_obj.account_name,
                    email=lead_obj.email,
                    phone=lead_obj.phone,
                    description=params.get("description"),
                    website=params.get("website"),
                    company=request.company,
                )
                account_object.billing_address_line = lead_obj.address_line
                account_object.billing_street = lead_obj.street
                account_object.billing_city = lead_obj.city
                account_object.billing_state = lead_obj.state
                account_object.billing_postcode = lead_obj.postcode
                account_object.billing_country = lead_obj.country
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)

                if params.getlist("assigned_to", []):
                    assigned_to_list = params.getlist("assigned_to")
                    current_site = get_current_site(request)
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(
                        recipients,
                        lead_obj.id,
                        domain=current_site.domain,
                        protocol=request.scheme,
                    )
                account_object.save()
            return Response({'error': False,
                             'message': 'Lead Created Successfully'},
                            status=status.HTTP_200_OK)
        return Response({'error': True,
                         'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class LeadDetailView(APIView):
    model = Lead
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Lead.objects.get(pk=pk)

    def get_context_data(self, **kwargs):
        context = {}
        user_assgn_list = [
            assigned_to.id for assigned_to in self.lead_obj.assigned_to.all()
        ]
        if self.request.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                raise PermissionDenied
        comments = Comment.objects.filter(
            lead__id=self.lead_obj.id).order_by("-id")
        attachments = Attachments.objects.filter(lead__id=self.lead_obj.id).order_by(
            "-id"
        )
        assigned_data = []
        for each in self.lead_obj.assigned_to.all():
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
        elif self.request.user != self.lead_obj.created_by:
            users_mention = [
                {"username": self.lead_obj.created_by.username}]
        else:
            users_mention = list(
                self.lead_obj.assigned_to.all().values("username"))
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            users = User.objects.filter(is_active=True, company=self.request.company).order_by(
                "email"
            )
        else:
            users = User.objects.filter(role="ADMIN", company=self.request.company).order_by(
                "email"
            )
        user_assgn_list = [
            assigned_to.id for assigned_to in self.lead_obj.get_assigned_users_not_in_teams
        ]

        if self.request.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                raise PermissionDenied
        team_ids = [user.id for user in self.lead_obj.get_team_users]
        all_user_ids = [user.id for user in users]
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = User.objects.filter(
            id__in=users_excluding_team_id)
        context["users"] = UserSerializer(users, many=True).data
        context["users_excluding_team"] = UserSerializer(
            users_excluding_team, many=True).data
        context["countries"] = COUNTRIES
        context["source"] = LEAD_SOURCE
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(company=self.request.company), many=True).data
        context.update(
            {
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "status": LEAD_STATUS,
                "countries": COUNTRIES,
                "users_mention": users_mention,
                "assigned_data": assigned_data,
                'lead_obj': LeadSerializer(self.lead_obj).data
            }
        )
        return context

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_list_get_params
    )
    def get(self, request, pk, **kwargs):
        self.lead_obj = self.get_object(pk)
        if self.lead_obj.company != request.company:
            return Response({'error': True}, status=status.HTTP_403_FORBIDDEN)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_create_post_params
    )
    def put(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        self.lead_obj = self.get_object(pk)
        if self.lead_obj.company != request.company:
            return Response({'error': True}, status=status.HTTP_403_FORBIDDEN)
        serializer = LeadCreateSerializer(
            data=params,
            instance=self.lead_obj,
            request_obj=request,
        )
        if serializer.is_valid():
            lead_obj = serializer.save()
            previous_assigned_to_users = list(
                lead_obj.assigned_to.all().values_list("id", flat=True)
            )
            lead_obj.tags.clear()
            if params.get("tags", ""):
                tags = params.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t)
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)
            if params.getlist("assigned_to", []):
                lead_obj.assigned_to.clear()
                lead_obj.assigned_to.add(*params.getlist("assigned_to"))
            else:
                lead_obj.assigned_to.clear()

            if params.getlist("teams", []):
                user_ids = Teams.objects.filter(
                    id__in=params.getlist("teams")
                ).values_list("users", flat=True)
                assinged_to_users_ids = lead_obj.assigned_to.all().values_list(
                    "id", flat=True
                )
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        lead_obj.assigned_to.add(user_id)

            if params.getlist("teams", []):
                lead_obj.teams.clear()
                lead_obj.teams.add(*params.getlist("teams"))
            else:
                lead_obj.teams.clear()

            current_site = get_current_site(request)
            assigned_to_list = list(
                lead_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) -
                              set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                lead_obj.id,
                domain=current_site.domain,
                protocol=request.scheme,
            )
            # update_leads_cache.delay()
            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    "lead_attachment").name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.save()

            if params.get("status") == "converted":
                account_object = Account.objects.create(
                    created_by=request.user,
                    name=lead_obj.account_name,
                    email=lead_obj.email,
                    phone=lead_obj.phone,
                    description=params.get("description"),
                    website=params.get("website"),
                    lead=lead_obj,
                    company=request.company,
                )
                account_object.billing_address_line = lead_obj.address_line
                account_object.billing_street = lead_obj.street
                account_object.billing_city = lead_obj.city
                account_object.billing_state = lead_obj.state
                account_object.billing_postcode = lead_obj.postcode
                account_object.billing_country = lead_obj.country
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)
                if params.getlist("assigned_to", []):
                    # account_object.assigned_to.add(*params.getlist('assigned_to'))
                    assigned_to_list = params.getlist("assigned_to")
                    current_site = get_current_site(request)
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(
                        recipients,
                        lead_obj.id,
                        domain=current_site.domain,
                        protocol=request.scheme,
                    )

                for comment in lead_obj.leads_comments.all():
                    comment.account = account_object
                    comment.save()
                account_object.save()
            return Response({'error': False,
                             'message': 'Lead updated Successfully'},
                            status=status.HTTP_200_OK)
        return Response({'error': True, 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_list_get_params
    )
    def delete(self, request, pk, **kwargs):
        self.object = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.created_by
        ) and self.object.company == request.company:
            self.object.delete()
            return Response({'error': False,
                             'message': 'Lead deleted Successfully'},
                            status=status.HTTP_200_OK)
        return Response({'error': True,
                         'message': "you don't have permission to delete this lead"},
                        status=status.HTTP_403_FORBIDDEN)
