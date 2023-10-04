from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER
)

organization_params = [
    organization_params_in_header,
]

user_list_params = [
    organization_params_in_header,
    OpenApiParameter("email",  OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter(
        "role", OpenApiTypes.STR, OpenApiParameter.QUERY,enum=["ADMIN", "USER"]
    ),
    OpenApiParameter(
        "status",
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        enum=["Active", "In Active"],
    ),
]

document_get_params = [
    organization_params_in_header,
    OpenApiParameter("title", OpenApiTypes.STR,OpenApiParameter.QUERY),
    OpenApiParameter(
        "status",
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        enum=["Active", "In Active"],
    ),
    OpenApiParameter("shared_to", OpenApiTypes.STR,OpenApiParameter.QUERY),
]

