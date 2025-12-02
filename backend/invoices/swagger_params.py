from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

company_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER, required=True
)

organization_params = [company_params_in_header]

invoice_list_get_params = organization_params + [
    OpenApiParameter(
        "invoice_title_or_number", OpenApiTypes.STR, OpenApiParameter.QUERY
    ),
    OpenApiParameter("created_by", OpenApiTypes.INT, OpenApiParameter.QUERY),
    OpenApiParameter("assigned_users", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("status", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("total_amount", OpenApiTypes.STR, OpenApiParameter.QUERY),
]

invoice_detail_post_params = organization_params + [
    OpenApiParameter("invoice_attachment", OpenApiTypes.BINARY, OpenApiParameter.QUERY),
    OpenApiParameter("comment", OpenApiTypes.STR, OpenApiParameter.QUERY),
]

invoice_delete_params = organization_params

invoice_create_post_params = organization_params + [
    OpenApiParameter(
        "invoice_title", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True
    ),
    OpenApiParameter("status", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("from_address_line", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("from_street", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("from_city", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("from_state", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("from_postcode", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("from_country", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("to_address_line", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("to_street", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("to_city", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("to_state", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("to_postcode", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("to_country", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("name", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("email", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True),
    OpenApiParameter("phone", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("due_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
    OpenApiParameter(
        "currency", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True
    ),
    OpenApiParameter("teams", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("assigned_to", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("accounts", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("quality_hours", OpenApiTypes.INT, OpenApiParameter.QUERY),
    OpenApiParameter("rate", OpenApiTypes.INT, OpenApiParameter.QUERY),
    OpenApiParameter("tax", OpenApiTypes.INT, OpenApiParameter.QUERY),
    OpenApiParameter("total_amount", OpenApiTypes.INT, OpenApiParameter.QUERY),
    OpenApiParameter("details", OpenApiTypes.STR, OpenApiParameter.QUERY),
]

invoice_comment_edit_params = organization_params + [
    OpenApiParameter("comment", OpenApiTypes.STR, OpenApiParameter.QUERY),
]
