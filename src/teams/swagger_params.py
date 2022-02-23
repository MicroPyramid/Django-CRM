from drf_yasg import openapi

organization_params_in_header = openapi.Parameter(
    'org', openapi.IN_HEADER, required=True, type=openapi.TYPE_INTEGER)

organization_params = [
    organization_params_in_header,
]

teams_list_get_params = [
    organization_params_in_header,
    openapi.Parameter("team_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("created_by", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_users", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

teams_create_post_params = [
    organization_params_in_header,
    openapi.Parameter(
        "name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "assign_users", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
]
