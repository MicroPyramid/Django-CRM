from drf_yasg import openapi

organization_params_in_header = openapi.Parameter(
    "org", openapi.IN_HEADER, required=True, type=openapi.TYPE_INTEGER
)

organization_params = [
    organization_params_in_header,
]

opportunity_list_get_params = [
    organization_params_in_header,
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("account", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("stage", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("lead_source", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("tags", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

opportunity_detail_get_params = [
    organization_params_in_header,
    openapi.Parameter(
        "opportunity_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

opportunity_create_post_params = [
    organization_params_in_header,
    openapi.Parameter(
        "name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("account", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("amount", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("currency", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("stage", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("lead_source", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("probability", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("contacts", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "due_date", openapi.IN_QUERY, type=openapi.FORMAT_DATE, example="2021-01-13"
    ),
    openapi.Parameter("tags", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "opportunity_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
]

opportunity_comment_edit_params = [
    organization_params_in_header,
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]
