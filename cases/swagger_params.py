from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    "company", openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING
)

cases_list_get_params = [
    company_params_in_header,
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("status", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("priority", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("account", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

cases_detail_get_params = [
    company_params_in_header,
    openapi.Parameter(
        "case_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

cases_delete_params = [
    company_params_in_header,
]

cases_create_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "status", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        "priority", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter("type_of_case", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "closed_on",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        format="date",
        required=True,
    ),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("account", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter(
        "case_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("contacts", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

cases_comment_edit_params = [
    company_params_in_header,
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]
