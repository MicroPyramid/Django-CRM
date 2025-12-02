from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER
)

organization_params = [
    organization_params_in_header,
]

contact_list_get_params = [
    organization_params_in_header,
    OpenApiParameter("name", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("city", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("assigned_to", OpenApiTypes.STR, OpenApiParameter.QUERY),
]

contact_create_post_params = [
    organization_params_in_header,
    OpenApiParameter("salutation", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("first_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("last_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("date_of_birth", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("organization", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("title", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("email", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("secondary_email", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("phone", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("secondary_number", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("department", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("language", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("do_not_call", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
    OpenApiParameter("address_line", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("street", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("city", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("state", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("pincode", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("country", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("description", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("linkedin_url", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("facebook_url", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("twitter_username", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("teams", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("assigned_to", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("contact_attachment", OpenApiTypes.BINARY, OpenApiParameter.QUERY),
]
