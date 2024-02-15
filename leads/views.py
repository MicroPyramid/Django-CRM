from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account, Tags
from common.models import APISettings, Attachments, Comment, Profile

#from common.external_auth import CustomDualAuthentication
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    LeadCommentSerializer,
    ProfileSerializer,
)
from .forms import LeadListForm
from .models import Company,Lead
from common.utils import COUNTRIES, INDCHOICES, LEAD_SOURCE, LEAD_STATUS
from contacts.models import Contact
from leads import swagger_params1
from leads.forms import LeadListForm
from leads.models import Company, Lead
from leads.serializer import (
    CompanySerializer,
    CompanySwaggerSerializer,
    LeadCreateSerializer,
    LeadSerializer,
    TagsSerializer,
    LeadCreateSwaggerSerializer,
    LeadDetailEditSwaggerSerializer,
    LeadCommentEditSwaggerSerializer,
    CreateLeadFromSiteSwaggerSerializer,
    LeadUploadSwaggerSerializer
)
from common.models import User
from leads.tasks import (
    create_lead_from_file,
    send_email_to_assigned_user,
    send_lead_assigned_emails,
)
from teams.models import Teams
from teams.serializer import TeamsSerializer


class LeadListView(APIView, LimitOffsetPagination):
    model = Lead
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = (
            self.model.objects.filter(org=self.request.profile.org)
            .exclude(status="converted")
            .select_related("created_by")
            .prefetch_related( 
                "tags",
                "assigned_to",
            )
        ).order_by("-id")
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile])
                | Q(created_by=self.request.profile.user)
            )

        if params:
            if params.get("name"):
                queryset = queryset.filter(
                    Q(first_name__icontains=params.get("name"))
                    & Q(last_name__icontains=params.get("name"))
                )
            if params.get("title"):
                queryset = queryset.filter(title__icontains=params.get("title"))
            if params.get("source"):
                queryset = queryset.filter(source=params.get("source"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.get("assigned_to")
                )
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            if params.get("tags"):
                queryset = queryset.filter(tags__in=params.get("tags"))
            if params.get("city"):
                queryset = queryset.filter(city__icontains=params.get("city"))
            if params.get("email"):
                queryset = queryset.filter(email__icontains=params.get("email"))
        context = {}
        queryset_open = queryset.exclude(status="closed")
        results_leads_open = self.paginate_queryset(
            queryset_open.distinct(), self.request, view=self
        )
        open_leads = LeadSerializer(results_leads_open, many=True).data
        if results_leads_open:
            offset = queryset_open.filter(id__gte=results_leads_open[-1].id).count()
            if offset == queryset_open.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context["open_leads"] = {
            "leads_count": self.count,
            "open_leads": open_leads,
            "offset": offset,
        }

        queryset_close = queryset.filter(status="closed")
        results_leads_close = self.paginate_queryset(
            queryset_close.distinct(), self.request, view=self
        )
        close_leads = LeadSerializer(results_leads_close, many=True).data
        if results_leads_close:
            offset = queryset_close.filter(id__gte=results_leads_close[-1].id).count()
            if offset == queryset_close.count():
                offset = None
        else:
            offset = 0

        context["close_leads"] = {
            "leads_count": self.count,
            "close_leads": close_leads,
            "offset": offset,
        }
        contacts = Contact.objects.filter(org=self.request.profile.org).values(
            "id", "first_name"
        )

        context["contacts"] = contacts
        context["status"] = LEAD_STATUS
        context["source"] = LEAD_SOURCE
        context["companies"] = CompanySerializer(
            Company.objects.filter(org=self.request.profile.org), many=True
        ).data
        context["tags"] = TagsSerializer(Tags.objects.all(), many=True).data

        users = Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
            "id", "user__email"
        )
        context["users"] = users
        context["countries"] = COUNTRIES
        context["industries"] = INDCHOICES
        return context

    @extend_schema(tags=["Leads"], parameters=swagger_params1.lead_list_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Leads"],description="Leads Create", parameters=swagger_params1.organization_params,request=LeadCreateSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):

        print('test')
        data = request.data
        serializer = LeadCreateSerializer(data=data, request_obj=request)
        if serializer.is_valid():
            lead_obj = serializer.save(created_by=request.profile.user
            , org=request.profile.org)
            if data.get("tags",None):
                tags = data.get("tags")
                for t in tags:
                    tag = Tags.objects.filter(slug=t.lower())
                    if tag.exists():
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)

            if data.get("contacts",None):
                obj_contact = Contact.objects.filter(
                    id__in=data.get("contacts"), org=request.profile.org
                )
                lead_obj.contacts.add(*obj_contact)

            recipients = list(lead_obj.assigned_to.all().values_list("id", flat=True))
            send_email_to_assigned_user.delay(
                recipients,
                lead_obj.id,
            )

            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile.user
                attachment.file_name = request.FILES.get("lead_attachment").name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.save()

            if data.get("teams",None):
                teams_list = data.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                lead_obj.teams.add(*teams)

            if data.get("assigned_to",None):
                assinged_to_list = data.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org
                )
                lead_obj.assigned_to.add(*profiles)

            if data.get("status") == "converted":
                account_object = Account.objects.create(
                    created_by=request.profile.user,
                    name=lead_obj.account_name,
                    email=lead_obj.email,
                    phone=lead_obj.phone,
                    description=data.get("description"),
                    website=data.get("website"),
                    org=request.profile.org,
                )

                account_object.billing_address_line = lead_obj.address_line
                account_object.billing_street = lead_obj.street
                account_object.billing_city = lead_obj.city
                account_object.billing_state = lead_obj.state
                account_object.billing_postcode = lead_obj.postcode
                account_object.billing_country = lead_obj.country
                comments = Comment.objects.filter(lead=self.lead_obj)
                if comments.exists():
                    for comment in comments:
                        comment.account_id = account_object.id
                attachments = Attachments.objects.filter(lead=self.lead_obj)
                if attachments.exists():
                    for attachment in attachments:
                        attachment.account_id = account_object.id
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)

                if data.get("assigned_to",None):
                    assigned_to_list = data.getlist("assigned_to")
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(
                        recipients,
                        lead_obj.id,
                    )
                return Response(
                    {
                        "error": False,
                        "message": "Lead Converted to Account Successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": False, "message": "Lead Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LeadDetailView(APIView):
    model = Lead
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Lead, id=pk)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        context = {}
        user_assgn_list = [
            assigned_to.id for assigned_to in self.lead_obj.assigned_to.all()
        ]
        if self.request.profile.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.profile.user)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comments = Comment.objects.filter(lead=self.lead_obj).order_by("-id")
        attachments = Attachments.objects.filter(lead=self.lead_obj).order_by("-id")
        assigned_data = []
        for each in self.lead_obj.assigned_to.all():
            assigned_dict = {}
            assigned_dict["id"] = each.id
            assigned_dict["name"] = each.user.email
            assigned_data.append(assigned_dict)

        if self.request.user.is_superuser or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
                    "user__email"
                )
            )
        elif self.request.profile.user != self.lead_obj.created_by:
            users_mention = [{"username": self.lead_obj.created_by.username}]
        else:
            users_mention = list(
                self.lead_obj.assigned_to.all().values("user__email")
            )
        if self.request.profile.role == "ADMIN" or self.request.user.is_superuser:
            users = Profile.objects.filter(
                is_active=True, org=self.request.profile.org
            ).order_by("user__email")
        else:
            users = Profile.objects.filter(role="ADMIN", org=self.request.profile.org).order_by(
                "user__email"
            )
        user_assgn_list = [
            assigned_to.id
            for assigned_to in self.lead_obj.get_assigned_users_not_in_teams
        ]

        if self.request.profile.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        team_ids = [user.id for user in self.lead_obj.get_team_users]
        all_user_ids = [user.id for user in users]
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = Profile.objects.filter(id__in=users_excluding_team_id)
        context.update(
            {
                "lead_obj": LeadSerializer(self.lead_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": LeadCommentSerializer(comments, many=True).data,
                "users_mention": users_mention,
                "assigned_data": assigned_data,
            }
        )
        context["users"] = ProfileSerializer(users, many=True).data
        context["users_excluding_team"] = ProfileSerializer(
            users_excluding_team, many=True
        ).data
        context["source"] = LEAD_SOURCE
        context["status"] = LEAD_STATUS
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(org=self.request.profile.org), many=True
        ).data
        context["countries"] = COUNTRIES

        return context

    @extend_schema(tags=["Leads"],parameters=swagger_params1.organization_params,description="Lead Detail")
    def get(self, request, pk, **kwargs):
        self.lead_obj = self.get_object(pk)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params,request=LeadDetailEditSwaggerSerializer)
    def post(self, request, pk, **kwargs):
        params = request.data

        context = {}
        self.lead_obj = Lead.objects.get(pk=pk)
        if self.lead_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile.user == self.lead_obj.created_by)
                or (self.request.profile in self.lead_obj.assigned_to.all())
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
                    lead_id=self.lead_obj.id,
                    commented_by_id=self.request.profile.id,
                )

            if self.request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = User.objects.get(id=self.request.profile.user.id)

                attachment.file_name = self.request.FILES.get("lead_attachment").name
                attachment.lead = self.lead_obj
                attachment.attachment = self.request.FILES.get("lead_attachment")
                attachment.save()

        comments = Comment.objects.filter(lead__id=self.lead_obj.id).order_by("-id")
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

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params,request=LeadCreateSwaggerSerializer)
    def put(self, request, pk, **kwargs):
        params = request.data
        self.lead_obj = self.get_object(pk)
        if self.lead_obj.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
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
                tags = params.get("tags")
                # for t in tags:
                #     tag,_ = Tags.objects.get_or_create(name=t)
                #     lead_obj.tags.add(tag)
                for t in tags:
                    tag = Tags.objects.filter(slug=t.lower())
                    if tag.exists():
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)

            assigned_to_list = list(
                lead_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                lead_obj.id,
            )
            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile.user
                attachment.file_name = request.FILES.get("lead_attachment").name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.save()

            lead_obj.contacts.clear()
            if params.get("contacts"):
                obj_contact = Contact.objects.filter(
                    id=params.get("contacts"), org=request.profile.org
                )
                lead_obj.contacts.add(obj_contact)

            lead_obj.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                lead_obj.teams.add(*teams)

            lead_obj.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org
                )
                lead_obj.assigned_to.add(*profiles)

            if params.get("status") == "converted":
                account_object = Account.objects.create(
                    created_by=request.profile.user,
                    name=lead_obj.account_name,
                    email=lead_obj.email,
                    phone=lead_obj.phone,
                    description=params.get("description"),
                    website=params.get("website"),
                    lead=lead_obj,
                    org=request.profile.org,
                )
                account_object.billing_address_line = lead_obj.address_line
                account_object.billing_street = lead_obj.street
                account_object.billing_city = lead_obj.city
                account_object.billing_state = lead_obj.state
                account_object.billing_postcode = lead_obj.postcode
                account_object.billing_country = lead_obj.country
                comments = Comment.objects.filter(lead=self.lead_obj)
                if comments.exists():
                    for comment in comments:
                        comment.account_id = account_object.id
                attachments = Attachments.objects.filter(lead=self.lead_obj)
                if attachments.exists():
                    for attachment in attachments:
                        attachment.account_id = account_object.id
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)
                if params.get("assigned_to"):
                    # account_object.assigned_to.add(*params.getlist('assigned_to'))
                    assigned_to_list = params.get("assigned_to")
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(
                        recipients,
                        lead_obj.id,
                    )

                for comment in lead_obj.leads_comments.all():
                    comment.account = account_object
                    comment.save()
                account_object.save()
                return Response(
                    {
                        "error": False,
                        "message": "Lead Converted to Account Successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": False, "message": "Lead updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Leads"],parameters=swagger_params1.organization_params, description="Lead Delete")
    def delete(self, request, pk, **kwargs):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile.user
             == self.object.created_by
        ) and self.object.org == request.profile.org:
            self.object.delete()
            return Response(
                {"error": False, "message": "Lead deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": "you don't have permission to delete this lead"},
            status=status.HTTP_403_FORBIDDEN,
        )


class LeadUploadView(APIView):
    model = Lead
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params,request=LeadUploadSwaggerSerializer)
    def post(self, request, *args, **kwargs):
        lead_form = LeadListForm(request.POST, request.FILES)
        if lead_form.is_valid():
            create_lead_from_file.delay(
                lead_form.validated_rows,
                lead_form.invalid_rows,
                request.profile.id,
                request.get_host(),
                request.profile.org.id,
            )
            return Response(
                {"error": False, "message": "Leads created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": lead_form.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LeadCommentView(APIView):
    model = Comment
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params,request=LeadCommentEditSwaggerSerializer)
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = LeadCommentSerializer(obj, data=params)
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
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params)
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


class LeadAttachmentView(APIView):
    model = Attachments
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile.user == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class CreateLeadFromSite(APIView):
    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,request=CreateLeadFromSiteSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        api_key = params.get("apikey")
        # api_setting = APISettings.objects.filter(
        #     website=website_address, apikey=api_key).first()
        api_setting = APISettings.objects.filter(apikey=api_key).first()
        if not api_setting:
            return Response(
                {
                    "error": True,
                    "message": "You don't have permission, please contact the admin!.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if api_setting and params.get("email") and params.get("title"):
            # user = User.objects.filter(is_admin=True, is_active=True).first()
            user = api_setting.created_by
            lead = Lead.objects.create(
                title=params.get("title"),
                first_name=params.get("first_name"),
                last_name=params.get("last_name"),
                status="assigned",
                source=api_setting.website,
                description=params.get("message"),
                email=params.get("email"),
                phone=params.get("phone"),
                is_active=True,
                created_by=user,
                org=api_setting.org,
            )
            lead.assigned_to.add(user)
            # Send Email to Assigned Users
            site_address = request.scheme + "://" + request.META["HTTP_HOST"]
            send_lead_assigned_emails.delay(lead.id, [user.id], site_address)
            # Create Contact
            try:
                contact = Contact.objects.create(
                    first_name=params.get("title"),
                    email=params.get("email"),
                    phone=params.get("phone"),
                    description=params.get("message"),
                    created_by=user,
                    is_active=True,
                    org=api_setting.org,
                )
                contact.assigned_to.add(user)

                lead.contacts.add(contact)
            except Exception:
                pass

            return Response(
                {"error": False, "message": "Lead Created sucessfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "message": "Invalid data"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CompaniesView(APIView):

    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["Company"],parameters=swagger_params1.organization_params)
    def get(self, request, *args, **kwargs):
        try:
            companies=Company.objects.filter(org=request.profile.org)
            serializer=CompanySerializer(companies,many=True)
            return Response(
                    {"error": False, "data": serializer.data},
                    status=status.HTTP_200_OK,
                )
        except:
            return Response(
                {"error": True, "message": "Organization is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )


    @extend_schema(
        tags=["Company"],description="Company Create",parameters=swagger_params1.organization_params,request=CompanySwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        request.data['org'] = request.profile.org.id
        print(request.data)
        company=CompanySerializer(data=request.data)
        if Company.objects.filter(**request.data).exists():
            return Response(
                {"error": True, "message": "This data already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if company.is_valid():
            company.save()
            return Response(
                {"error": False, "message": "Company created successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": True, "message": company.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

class CompanyDetail(APIView):
   
    permission_classes = (IsAuthenticated,)

    
    def get_object(self, pk):
        try:
            return Company.objects.get(
                pk=pk
            )
        except Company.DoesNotExist:
            raise Http404

    @extend_schema(tags=["Company"],parameters=swagger_params1.organization_params)
    def get(self, request, pk, format=None):
        company = self.get_object(pk)
        serializer = CompanySerializer(company)
        return Response(
                {"error": False, "data": serializer.data},
                status=status.HTTP_200_OK,
            )
    @extend_schema(tags=["Company"],description="Company Update",parameters=swagger_params1.organization_params,request=CompanySerializer)
    def put(self, request, pk, format=None):
        company = self.get_object(pk)
        serializer = CompanySerializer(company, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"error": False, "data": serializer.data,'message': 'Updated Successfully'},
                status=status.HTTP_200_OK,
            )
        return Response(
                {"error": True,'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    @extend_schema(tags=["Company"],parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        company = self.get_object(pk)
        company.delete()
        return Response(
                {"error": False, 'message': 'Deleted successfully'},
                status=status.HTTP_200_OK,
            )
 