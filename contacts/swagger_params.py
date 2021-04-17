from drf_yasg import openapi

contact_list_get_params = [
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

contact_create_post_params = [
    openapi.Parameter(
        "first_name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "last_name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "phone", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "email", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("address_line", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("street", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("state", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("postcode", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("country", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("contact_attachment", openapi.IN_QUERY, type=openapi.TYPE_FILE),
]

contact_detail_get_params = [
    openapi.Parameter(
        "contact_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

contact_comment_edit_params = [
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]
