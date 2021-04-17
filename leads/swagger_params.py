from drf_yasg import openapi

lead_list_get_params = [
    openapi.Parameter("title", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("source", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("status", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("tags", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

lead_detail_get_params = [
    openapi.Parameter(
        "lead_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

lead_create_post_params = [
    openapi.Parameter(
        "title", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("first_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("last_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("account_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("phone", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("email", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "lead_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("website", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("status", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("source", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("address_line", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("street", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("state", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("postcode", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("country", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("tags", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

lead_upload_post_params = [
    openapi.Parameter(
        "leads_file",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
]

lead_comment_edit_params = [
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

create_lead_from_site = [
    openapi.Parameter(
        "apikey", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "title", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("first_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("last_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("phone", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "email", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        "source", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]
