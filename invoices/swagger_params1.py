from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params_in_header = organization_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER
)

organization_params = [
    organization_params_in_header,
]

invoice_list_get_params = [
    organization_params,
    OpenApiParameter(
        "invoice_title_or_number",OpenApiParameter.QUERY, OpenApiTypes.STR
    ),
    OpenApiParameter("created_by",OpenApiParameter.QUERY, OpenApiTypes.INT),
    OpenApiParameter("assigned_users",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("status",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("total_amount",OpenApiParameter.QUERY, OpenApiTypes.STR),
]

invoice_detail_post_params = [
    organization_params,
    OpenApiParameter(
        "invoice_attachment",
       OpenApiParameter.QUERY,
        type=openapi.TYPE_FILE,
    ),
    OpenApiParameter("comment",OpenApiParameter.QUERY, OpenApiTypes.STR),
]

invoice_delete_params = [
    organization_params,
]

invoice_create_post_params = [
    organization_params,
    OpenApiParameter(
        "invoice_title",OpenApiParameter.QUERY,  OpenApiTypes.STR, required=True,
    ),
    OpenApiParameter("status",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("from_address_line",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("from_street",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("from_city",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("from_state",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("from_postcode",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("from_country",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("to_address_line",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("to_street",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("to_city",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("to_state",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("to_postcode",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("to_country",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("name",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter(
        "email",OpenApiParameter.QUERY,  OpenApiTypes.STR, required=True,
    ),
    OpenApiParameter("phone",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter(
        "due_date",OpenApiParameter.QUERY, type=openapi.FORMAT_DATE, example="2021-02-28"
    ),
    OpenApiParameter(
        "currency",OpenApiParameter.QUERY, OpenApiTypes.STR,required=True,
    ),
    OpenApiParameter("teams",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("assigned_to",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("accounts",OpenApiParameter.QUERY, OpenApiTypes.STR),
    OpenApiParameter("quality_hours",OpenApiParameter.QUERY, OpenApiTypes.INT),
    OpenApiParameter("rate",OpenApiParameter.QUERY, OpenApiTypes.INT),
    OpenApiParameter("tax",OpenApiParameter.QUERY, OpenApiTypes.INT),
    OpenApiParameter("total_amount",OpenApiParameter.QUERY, OpenApiTypes.INT),
    OpenApiParameter("details",OpenApiParameter.QUERY, OpenApiTypes.STR),
]

invoice_comment_edit_params = [
    organization_params,
    OpenApiParameter("comment",OpenApiParameter.QUERY, OpenApiTypes.STR),
]
