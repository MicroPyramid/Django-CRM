from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params_in_header = organization_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER
)

organization_params = [
    organization_params_in_header,
]

teams_list_get_params = [
    organization_params_in_header,
    OpenApiParameter("team_name", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("created_by", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("assigned_users", OpenApiTypes.STR,OpenApiParameter.QUERY),
]
