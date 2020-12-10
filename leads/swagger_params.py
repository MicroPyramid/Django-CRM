from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    "company", openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING
)


lead_list_get_params = [company_params_in_header]

lead_create_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "title", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "first_name", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "last_name", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "email", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "phone", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "status", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "source", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "website", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "description", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "teams", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "address_line",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        "street", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "city", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "state", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "postcode", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "country", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "tags", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
]
