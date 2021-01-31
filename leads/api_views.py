from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from accounts.models import Account, Tags
from accounts.tasks import send_email_to_assigned_user
from leads import swagger_params
from common.models import User, Attachments, Comment
from common.utils import (
    COUNTRIES,
    LEAD_SOURCE,
    LEAD_STATUS
)
from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import (UserSerializer, CommentSerializer,
                               AttachmentsSerializer, LeadCommentSerializer)
from leads.models import Lead
from leads.forms import LeadListForm
from leads.serializer import LeadSerializer, LeadCreateSerializer, TagsSerializer
from leads.tasks import (
    create_lead_from_file,
    send_email_to_assigned_user,
    send_lead_assigned_emails,
    update_leads_cache,
)
from teams.serializer import TeamsSerializer
from teams.models import Teams
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
import json


class LeadListView(APIView):
    model = Lead
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
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
        if request_post:
            if request_post.get("name"):
                queryset = queryset.filter(
                    Q(first_name__icontains=request_post.get("name"))
                    & Q(last_name__icontains=request_post.get("name"))
                )
            if request_post.get("title"):
                queryset = queryset.filter(
                    title__icontains=request_post.get("title"))
            if request_post.get("source"):
                queryset = queryset.filter(
                    source=request_post.get("source"))
            if request_post.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=json.loads(request_post.get("assigned_to"))                )
            if request_post.get("status"):
                queryset = queryset.filter(
                    status=request_post.get("status"))
            if request_post.get("tags"):
                queryset = queryset.filter(
                    tags__in=json.loads(request_post.get("tags")))
            if request_post.get("city"):
                queryset = queryset.filter(
                    city__icontains=request_post.get("city"))
            if request_post.get("email"):
                queryset = queryset.filter(
                    email__icontains=request_post.get("email"))
        context = {}
        search = False
        if (
            params.get("title")
            or params.get("source")
            or params.get("assigned_to")
            or params.get("status")
            or params.get("tags")
        ):
            search = True
        context["search"] = search
        open_leads = queryset.exclude(status="closed").distinct()
        close_leads = queryset.filter(status="closed").distinct()       
        if search:
            context["open_leads"] = LeadSerializer(open_leads, many=True).data
            return context

        context["open_leads"] = LeadSerializer(open_leads, many=True).data
        context["close_leads"] = LeadSerializer(close_leads, many=True).data
        context["status"] = LEAD_STATUS
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
                queryset.values_list(
                    "tags",
                    flat=True,
                )
            )
        )

        context["tags"] = TagsSerializer(
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
        data = {}
        serializer = LeadCreateSerializer(
            data=params, request_obj=request)
        if serializer.is_valid():
            lead_obj = serializer.save(
                created_by=request.user, company=request.company)
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                # for t in tags:
                #     tag,_ = Tags.objects.get_or_create(name=t)
                #     lead_obj.tags.add(tag)
                for t in tags:
                    tag = Tags.objects.filter(slug=t.lower())
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)

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

            if self.request.user.role == "ADMIN":
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team,company=request.company)
                        if teams_ids:
                            lead_obj.teams.add(team)
                        else:
                            lead_obj.delete()
                            data["team"] = "Please enter valid Team"
                            return Response({"error": True, "errors":data})
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id, company=request.company)
                        if user:                            
                            lead_obj.assigned_to.add(user_id)
                        else:
                            lead_obj.delete()
                            data["assigned_to"] = "Please enter valid User"
                            return Response({"error": True, "errors":data})            
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
                comments = Comment.objects.filter(lead=self.lead_obj)
                if comments:
                    for comment in comments:
                        comment.account_id = account_object.id
                attachments = Attachments.objects.filter(lead=self.lead_obj)
                if attachments:
                    for attachment in attachments:
                        attachment.account_id = account_object.id
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)

                if params.get("assigned_to"):
                    assigned_to_list = json.loads(params.getlist("assigned_to"))
                    current_site = get_current_site(request)
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(
                        recipients,
                        lead_obj.id,
                        domain=current_site.domain,
                        protocol=request.scheme,
                    )
                return Response({"error": False,
                                 "message": "Lead Converted to Account Successfully"},
                                status=status.HTTP_200_OK)            
            return Response({"error": False,
                             "message": "Lead Created Successfully"},
                            status=status.HTTP_200_OK)
        return Response({"error": True,
                         "errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class LeadDetailView(APIView):
    model = Lead
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Lead.objects.get(pk=pk)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        context = {}
        user_assgn_list = [
            assigned_to.id for assigned_to in self.lead_obj.assigned_to.all()
        ]
        if self.request.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                return Response(
                    {"error": True,
                     "errors": "You do not have Permission to perform this action"}
                )
 
        comments = Comment.objects.filter(
            lead=self.lead_obj).order_by("-id")
        attachments = Attachments.objects.filter(lead=self.lead_obj).order_by(
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
                return Response(
                    {"error": True,
                     "errors": "You do not have Permission to perform this action"}
                )
        team_ids = [user.id for user in self.lead_obj.get_team_users]
        all_user_ids = [user.id for user in users]
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = User.objects.filter(
            id__in=users_excluding_team_id)
        context.update(
            {
                "lead_obj": LeadSerializer(self.lead_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": LeadCommentSerializer(comments, many=True).data,
                "users_mention": users_mention,
                "assigned_data": assigned_data,
            }
        )
        context["users"] = UserSerializer(users, many=True).data
        context["users_excluding_team"] = UserSerializer(
            users_excluding_team, many=True).data
        context["source"] = LEAD_SOURCE
        context["status"] = LEAD_STATUS
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(company=self.request.company), many=True).data
        context["countries"] = COUNTRIES

        return context

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_delete_params
    )
    def get(self, request, pk, **kwargs):
        self.lead_obj = self.get_object(pk)
        if self.lead_obj.company != request.company:
            return Response(
                {"error": True,
                 "errors": "User company doesnot match with header...."}
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_detail_get_params
    )
    def post(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        context = {}
        self.lead_obj = Lead.objects.get(pk=pk)
        if self.lead_obj.company != request.company:
            return Response(
                {"error": True,
                 "errors": "User company does not match with header...."}
            )

        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.lead_obj.created_by)
                or (self.request.user in self.lead_obj.assigned_to.all())
            ):
                return Response(
                    {"error": True,
                     "errors": "You do not have Permission to perform this action"},
                     status = status.HTTP_401_UNAUTHORIZED
                )
        comment_serializer = CommentSerializer(
            data=params)
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    lead_id = self.lead_obj.id,
                    commented_by_id = self.request.user.id,)
          
            if self.request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.user
                attachment.file_name = self.request.FILES.get(
                    "lead_attachment").name
                attachment.lead = self.lead_obj
                attachment.attachment = self.request.FILES.get("lead_attachment")
                attachment.save()

        comments = Comment.objects.filter(
            lead__id=self.lead_obj.id).order_by("-id")
        attachments = Attachments.objects.filter(lead__id=self.lead_obj.id).order_by(
            "-id"
        )
        context.update(
            {
                "lead_obj": LeadSerializer(self.lead_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": LeadCommentSerializer(comments, many=True).data,
            }
        )
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
        data = {}
        self.lead_obj = self.get_object(pk)
        if self.lead_obj.company != request.company:
            return Response(
                {"error": True,
                 "errors": "User company doesnot match with header...."}
            )
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
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                # for t in tags:
                #     tag,_ = Tags.objects.get_or_create(name=t)
                #     lead_obj.tags.add(tag)
                for t in tags:
                    tag = Tags.objects.filter(slug=t.lower())
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)

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
            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    "lead_attachment").name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.save()

            if self.request.user.role == "ADMIN":
                lead_obj.teams.clear()
                if params.get("teams"):                    
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team,company=request.company)
                        if teams_ids:
                            lead_obj.teams.add(team)
                        else:
                            lead_obj.delete()
                            data["team"] = "Please enter valid Team"
                            return Response({"error": True, "errors":data})
                else:
                    lead_obj.teams.clear()

                lead_obj.assigned_to.clear()
                if params.get("assigned_to"):                    
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id, company=request.company)
                        if user:                            
                            lead_obj.assigned_to.add(user_id)
                        else:
                            lead_obj.delete()
                            data["assigned_to"] = "Please enter valid User"
                            return Response({"error": True, "errors":data})
                else:
                    lead_obj.assigned_to.clear()   

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
                comments = Comment.objects.filter(lead=self.lead_obj)
                if comments:
                    for comment in comments:
                        comment.account_id = account_object.id
                attachments = Attachments.objects.filter(lead=self.lead_obj)
                if attachments:
                    for attachment in attachments:
                        attachment.account_id = account_object.id
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)
                if params.get("assigned_to"):
                    # account_object.assigned_to.add(*params.getlist('assigned_to'))
                    assigned_to_list = json.loads(params.get("assigned_to"))
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
                return Response({"error": False,
                                 "message": "Lead Converted to Account Successfully"},
                                status=status.HTTP_200_OK) 
            return Response({"error": False,
                             "message": "Lead updated Successfully"},
                            status=status.HTTP_200_OK)
        return Response({"error": True, "errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_delete_params
    )
    def delete(self, request, pk, **kwargs):
        self.object = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.created_by
        ) and self.object.company == request.company:
            self.object.delete()
            return Response({"error": False,
                             "message": "Lead deleted Successfully"},
                            status=status.HTTP_200_OK)
        return Response({"error": True,
                         "errors": "you don't have permission to delete this lead"},
                        status=status.HTTP_403_FORBIDDEN)

class LeadUploadView(APIView):
    model = Lead
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Leads"], manual_parameters=swagger_params.lead_upload_post_params
    )
    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            lead_form = LeadListForm(request.POST, request.FILES)
            if lead_form.is_valid():
                create_lead_from_file.delay(
                    lead_form.validated_rows,
                    lead_form.invalid_rows,
                    request.user.id,
                    request.get_host(),
                    request.company.id,
                )
                return Response(
                    {"error": False, "message": "Leads created Successfully"}, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"error": True, "errors": lead_form.errors}, status=status.HTTP_200_OK
                )

class LeadCommentView(APIView):
    model = Comment
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Leads"],
        manual_parameters=swagger_params.lead_comment_edit_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        obj = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == obj.commented_by
        ): 
            serializer = LeadCommentSerializer(
                obj, data=params)
            if params.get("comment"):
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {"error": False, "message":"Comment Submitted"},
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {"error": True, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response({
                    "error": True,
                    "errors": "User company doesnot match with header...."}
                )

    @swagger_auto_schema(
        tags=["Leads"], 
        manual_parameters=swagger_params.lead_delete_params
    )
    def delete(self, request, pk, format=None):        
        self.object = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.commented_by
        ):    
            self.object.delete()
            return Response({
                    "error": False,
                    "message": "Comment Deleted Successfully"},
                    status=status.HTTP_200_OK)
        else:
            return Response({
                "error": True,
                "errors": "You do not have permission to perform this action"}
            )

class LeadAttachmentView(APIView):
    model = Attachments
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Leads"], 
        manual_parameters=swagger_params.lead_delete_params
    )
    def delete(self, request, pk, format=None):        
        self.object = self.model.objects.get(pk=pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.created_by
        ):    
            self.object.delete()
            return Response({
                    "error": False,
                    "message": "Attachment Deleted Successfully"},
                    status=status.HTTP_200_OK)
        else:
            return Response({
                "error": True,
                "errors": "User company doesnot match with header...."}
            )