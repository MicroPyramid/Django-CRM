from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    "company", openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING
)

teams_list_get_params = [
    company_params_in_header,
    openapi.Parameter("team_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("created_by", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_users", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

teams_delete_params = [
    company_params_in_header,
]

teams_create_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "assign_users", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
]
