from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params_in_header = organization_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER
)

organization_params = [
    organization_params_in_header,
]


opportunity_list_get_params = [
    organization_params_in_header,
    OpenApiParameter("name", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("account", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("stage", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("lead_source", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("tags", OpenApiTypes.STR,OpenApiParameter.QUERY),
]

opportunity_detail_get_params = [
    organization_params_in_header,
    OpenApiParameter(
        "opportunity_attachment",
        OpenApiParameter.QUERY,
        OpenApiTypes.BINARY,
    ),
    OpenApiParameter("comment", OpenApiTypes.STR,OpenApiParameter.QUERY),
]

opportunity_comment_edit_params = [
    organization_params_in_header,
    OpenApiParameter("comment", OpenApiTypes.STR,OpenApiParameter.QUERY),
]
