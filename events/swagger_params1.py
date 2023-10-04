from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params_in_header = organization_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER
)

organization_params = [
    organization_params_in_header,
]

event_list_get_params = [
    organization_params_in_header,
    OpenApiParameter("name", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("created_by", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter("assigned_users", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter(
        "date_of_meeting",
        OpenApiParameter.QUERY,
        OpenApiTypes.DATE
    ),
]

event_detail_post_params = [
    organization_params_in_header,
    OpenApiParameter(
        "event_attachment",
        OpenApiParameter.QUERY,
        OpenApiTypes.BINARY
    ),
    OpenApiParameter("comment", OpenApiTypes.STR,OpenApiParameter.QUERY),
]

event_comment_edit_params = [
    organization_params_in_header,
    OpenApiParameter("comment", OpenApiTypes.STR,OpenApiParameter.QUERY),
]
