"""`/api/interactions/`: a record's timeline, logging, editing and deleting.

The route is core; each request is checked against the module of the record
it names, as the record's own routes would be, and a token needs that record's
own scope as well as `interactions:*`.
"""

from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.access import assert_case_write_access
from common.lookups import get_scoped_or_404
from common.models import PersonalAccessToken
from common.modules import module_is_available, module_off_response
from common.permissions import HasOrgContext
from common.scopes import ORG_API_KEY_SCOPES
from common.validators import uuid_param
from interactions.access import (
    home_module,
    is_read_only,
    may_change_interaction,
    scope_denial,
    visible_interactions_qs,
    visible_records,
)
from interactions.models import Interaction
from interactions.serializers import (
    ONE_RECORD,
    InteractionSerializer,
    InteractionWriteSerializer,
)
from interactions.service import (
    HOME_KEYS,
    change_interaction,
    delete_interaction,
    log_interaction,
)

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

READ_ONLY = "Enquiries, and interactions written by an integration, cannot be changed."
NOT_YOURS = "Only the person who logged this, or an admin, can change it."
NOT_FOUND = "No such record."


def _refuse(errors, code=status.HTTP_400_BAD_REQUEST):
    return Response({"error": True, "errors": errors}, status=code)


def _module_off(org, home):
    module = home_module(home)
    if module is not None and not module_is_available(org, module):
        return module_off_response(org, module)
    return None


def _token_scopes(request):
    """The scopes of the token behind `request`, or None for a signed-in
    session. The org API key reads with `ORG_API_KEY_SCOPES`."""
    if isinstance(request.auth, PersonalAccessToken):
        return request.auth.scopes
    if request.META.get("org_api_key_auth"):
        return ORG_API_KEY_SCOPES
    return None


def _scope_refused(request, home):
    """The 403 the middleware gives an out-of-scope token, or None."""
    denial = scope_denial(_token_scopes(request), request.method, home)
    return None if denial is None else Response({"detail": denial}, status=403)


def _count(params, name, default):
    """A non-negative integer query parameter; anything else is `default`."""
    try:
        value = int(params.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


def _out(interaction, profile):
    return InteractionSerializer(interaction, context={"profile": profile}).data


RECORD_PARAMS = [
    OpenApiParameter(name, OpenApiTypes.UUID, OpenApiParameter.QUERY)
    for name in HOME_KEYS
] + [
    OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
    OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY),
]


class InteractionListView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Interactions"],
        operation_id="interactions_list",
        parameters=RECORD_PARAMS,
    )
    def get(self, request):
        profile = request.profile
        named = [h for h in HOME_KEYS if request.query_params.get(h) not in (None, "")]
        if len(named) != 1:
            return _refuse({"non_field_errors": [ONE_RECORD]})
        home = named[0]
        pk = uuid_param(request.query_params, home)
        refused = _scope_refused(request, home) or _module_off(profile.org, home)
        if refused is not None:
            return refused
        if not visible_records(profile, home).filter(pk=pk).exists():
            raise Http404(NOT_FOUND)

        scopes = _token_scopes(request)
        readable = [h for h in HOME_KEYS if not scope_denial(scopes, "GET", h)]
        rows = (
            visible_interactions_qs(profile)
            .filter(**{f"{home}_id": pk}, home__in=readable)
            .select_related("logged_by__user")
            .order_by("-occurred_at", "-created_at", "-pk")
        )
        limit = min(_count(request.query_params, "limit", DEFAULT_LIMIT), MAX_LIMIT)
        offset = _count(request.query_params, "offset", 0)
        page = rows[offset : offset + limit]
        return Response(
            {
                "interactions": InteractionSerializer(
                    page, many=True, context={"profile": profile}
                ).data,
                "count": rows.count(),
            }
        )

    @extend_schema(
        tags=["Interactions"],
        operation_id="interactions_create",
        request=InteractionWriteSerializer,
        responses={201: InteractionSerializer},
    )
    def post(self, request):
        profile = request.profile
        serializer = InteractionWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return _refuse(serializer.errors)
        values = dict(serializer.validated_data)
        home = values.pop("home")
        pk = values.pop(home)
        refused = _scope_refused(request, home) or _module_off(profile.org, home)
        if refused is not None:
            return refused
        record = visible_records(profile, home).filter(pk=pk).first()
        if record is None:
            raise Http404(NOT_FOUND)
        if home == "case":
            # A watcher may read a ticket but not work it.
            assert_case_write_access(profile, record)

        interaction = log_interaction(
            profile.org, home=home, record=record, logged_by=profile, **values
        )
        return Response(_out(interaction, profile), status=status.HTTP_201_CREATED)


class InteractionDetailView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def _changeable(self, request, pk):
        """The interaction, or a 404 when its home is hidden from the caller,
        and the 403 to answer when they may not change it."""
        profile = request.profile
        interaction = get_scoped_or_404(
            Interaction,
            pk,
            profile.org,
            pk__in=visible_interactions_qs(profile).values("pk"),
        )
        refused = _scope_refused(request, interaction.home)
        if refused is not None:
            return interaction, refused
        if is_read_only(interaction):
            return interaction, _refuse(READ_ONLY, status.HTTP_403_FORBIDDEN)
        if not may_change_interaction(profile, interaction):
            return interaction, _refuse(NOT_YOURS, status.HTTP_403_FORBIDDEN)
        return interaction, None

    @extend_schema(
        tags=["Interactions"],
        operation_id="interactions_update",
        request=InteractionWriteSerializer,
        responses={200: InteractionSerializer},
    )
    def patch(self, request, pk):
        interaction, refused = self._changeable(request, pk)
        if refused is not None:
            return refused
        serializer = InteractionWriteSerializer(
            interaction, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return _refuse(serializer.errors)
        change_interaction(interaction, serializer.validated_data)
        return Response(_out(interaction, request.profile))

    @extend_schema(tags=["Interactions"], operation_id="interactions_delete")
    def delete(self, request, pk):
        interaction, refused = self._changeable(request, pk)
        if refused is not None:
            return refused
        delete_interaction(interaction)
        return Response(status=status.HTTP_204_NO_CONTENT)
