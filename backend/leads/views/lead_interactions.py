from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.lookups import get_scoped_or_404
from common.models import APISettings, Attachments, Comment
from common.permissions import HasOrgContext, is_org_admin
from common.serializer import LeadCommentSerializer
from contacts.models import Contact
from leads import swagger_params
from leads.forms import LeadListForm
from leads.models import Lead
from leads.serializer import (
    CreateLeadFromSiteSwaggerSerializer,
    LeadCommentEditSwaggerSerializer,
    LeadUploadSwaggerSerializer,
)
from leads.tasks import create_lead_from_file, send_lead_assigned_emails

# Matches the contacts and cases importers, and the UI hint beside the control.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def _can_import(profile) -> bool:
    """Mass-create requires admin or explicit sales-access permission.

    Same rule as `contacts.import_views._can_import` and its cases twin. This
    endpoint predates both and never grew the check, so any member could
    bulk-create leads through it.
    """
    if profile is None:
        return False
    if getattr(profile, "role", None) == "ADMIN":
        return True
    if getattr(profile, "is_admin", False):
        return True
    return bool(getattr(profile, "has_sales_access", False))


class LeadUploadView(APIView):
    model = Lead
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadUploadSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="LeadUploadResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        if not _can_import(request.profile):
            return Response(
                {"error": True, "errors": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )
        # The cap is measured against the bytes actually read, not against
        # `upload.size`, which for an in-memory upload derives from a
        # client-supplied Content-Length and can understate the body.
        upload = request.FILES.get("leads_file")
        if upload is not None:
            file_bytes = upload.read()
            upload.seek(0)
            if len(file_bytes) > MAX_UPLOAD_BYTES:
                return Response(
                    {"error": True, "errors": "File exceeds the 5 MB upload limit"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return get_scoped_or_404(self.model, pk, self.request.profile.org)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadCommentEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="LeadCommentUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            is_org_admin(request.profile)
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

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadCommentEditSwaggerSerializer,
        description="Partial Comment Update",
        responses={
            200: inline_serializer(
                name="LeadCommentPatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to a comment."""
        params = request.data
        obj = self.get_object(pk)
        if (
            is_org_admin(request.profile)
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = LeadCommentSerializer(obj, data=params, partial=True)
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
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="LeadCommentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            is_org_admin(request.profile)
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
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="LeadAttachmentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, format=None):
        # Was `objects.get(pk=pk)`: no org filter, so an admin of any org could
        # delete any attachment in the system by id, and a missing or malformed
        # id raised out of the view as a 500 instead of answering 404. The
        # comment view above already scopes its lookup, as do the accounts,
        # contacts, cases, tasks, tags and teams equivalents.
        self.object = get_scoped_or_404(self.model, pk, request.profile.org)
        if (
            is_org_admin(request.profile)
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
        parameters=swagger_params.organization_params,
        request=CreateLeadFromSiteSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="CreateLeadFromSiteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
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

        if api_setting and params.get("email"):
            # user = User.objects.filter(is_admin=True, is_active=True).first()
            user = api_setting.created_by
            lead = Lead.objects.create(
                salutation=params.get(
                    "title"
                ),  # 'title' param maps to salutation for backwards compatibility
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
            # Send Email to Assigned Users. The task builds its own link from
            # FRONTEND_URL; it used to be handed a base derived from this
            # request's Host header, which named the API rather than the web
            # app and let a caller of this endpoint influence the link.
            send_lead_assigned_emails.delay(lead.id, [user.id], str(api_setting.org.id))
            # Create Contact
            try:
                contact = Contact.objects.create(
                    first_name=params.get("first_name") or "",
                    last_name=params.get("last_name") or "",
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
