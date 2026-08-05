"""Schema-only parameter lists for drf-spectacular.

There is no ``org`` request header. Org context comes from the JWT's ``org_id``
claim, from the org that owns a personal access token, or from the org that
owns an API key, all resolved in ``common/middleware/get_company.py``. Nothing
anywhere reads ``request.headers["org"]``.

Every one of these files used to open by declaring
``OpenApiParameter("org", ..., HEADER)`` and putting it at the head of each
list, so the published schema told 101 operations' worth of integrators to send
a header the server ignores. The parameter is gone; ``organization_params``
stays as an empty list because 101 views name it, and an empty list is what
those views should now contribute to the schema.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params = []

user_list_params = [
    OpenApiParameter("email", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter(
        "role", OpenApiTypes.STR, OpenApiParameter.QUERY, enum=["ADMIN", "USER"]
    ),
    OpenApiParameter(
        "status",
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        enum=["Active", "In Active"],
    ),
]

document_get_params = [
    OpenApiParameter("title", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter(
        "status",
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        enum=["Active", "In Active"],
    ),
    OpenApiParameter("shared_to", OpenApiTypes.STR, OpenApiParameter.QUERY),
]

# Teams params (merged from teams app)
teams_list_get_params = [
    OpenApiParameter("team_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("created_by", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("assigned_users", OpenApiTypes.STR, OpenApiParameter.QUERY),
]
