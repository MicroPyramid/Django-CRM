from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from accounts.serializer import AccountSerializer
from common import serializer, swagger_params
from common.models import Activity
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from leads.models import Lead
from leads.serializer import LeadSerializer
from opportunity.models import Opportunity
from opportunity.serializer import OpportunitySerializer


class ApiHomeView(APIView):

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["home"],
        parameters=swagger_params.organization_params,
        responses={200: inline_serializer(
            name="ApiHomeResponse",
            fields={
                "accounts_count": serializers.IntegerField(),
                "contacts_count": serializers.IntegerField(),
                "leads_count": serializers.IntegerField(),
                "opportunities_count": serializers.IntegerField(),
                "accounts": AccountSerializer(many=True),
                "contacts": ContactSerializer(many=True),
                "leads": LeadSerializer(many=True),
                "opportunities": OpportunitySerializer(many=True),
            }
        )},
    )
    def get(self, request, format=None):
        accounts = Account.objects.filter(is_active=True, org=request.profile.org)
        contacts = Contact.objects.filter(org=request.profile.org)
        leads = Lead.objects.filter(org=request.profile.org).exclude(
            Q(status="converted") | Q(status="closed")
        )
        opportunities = Opportunity.objects.filter(org=request.profile.org)

        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            accounts = accounts.filter(
                Q(assigned_to=self.request.profile)
                | Q(created_by=self.request.profile.user)
            )
            contacts = contacts.filter(
                Q(assigned_to__id__in=self.request.profile)
                | Q(created_by=self.request.profile.user)
            )
            leads = leads.filter(
                Q(assigned_to__id__in=self.request.profile)
                | Q(created_by=self.request.profile.user)
            ).exclude(status="closed")
            opportunities = opportunities.filter(
                Q(assigned_to__id__in=self.request.profile)
                | Q(created_by=self.request.profile.user)
            )
        context = {}
        context["accounts_count"] = accounts.count()
        context["contacts_count"] = contacts.count()
        context["leads_count"] = leads.count()
        context["opportunities_count"] = opportunities.count()
        context["accounts"] = AccountSerializer(accounts, many=True).data
        context["contacts"] = ContactSerializer(contacts, many=True).data
        context["leads"] = LeadSerializer(leads, many=True).data
        context["opportunities"] = OpportunitySerializer(opportunities, many=True).data
        return Response(context, status=status.HTTP_200_OK)


class ActivityListView(APIView):
    """
    Get recent activities for the organization
    Returns the last 10 activities by default
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["activities"],
        parameters=swagger_params.organization_params
        + [
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of activities to return (default: 10, max: 50)",
            ),
            OpenApiParameter(
                name="entity_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by entity type (Account, Lead, Contact, etc.)",
            ),
        ],
        responses={200: serializer.ActivitySerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get query params
        limit = min(int(request.query_params.get("limit", 10)), 50)
        entity_type = request.query_params.get("entity_type", None)

        # Query activities for this organization
        queryset = Activity.objects.filter(org=request.profile.org)

        # Filter by entity type if specified
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        # Get most recent activities
        activities = queryset.select_related("user", "user__user")[:limit]

        # Serialize
        activities_data = serializer.ActivitySerializer(activities, many=True).data

        return Response(
            {
                "error": False,
                "count": len(activities_data),
                "activities": activities_data,
            },
            status=status.HTTP_200_OK,
        )
