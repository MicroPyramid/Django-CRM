from drf_yasg import openapi

organization_params_in_header = openapi.Parameter(
    'org', openapi.IN_HEADER, required=True, type=openapi.TYPE_INTEGER)

organization_params = [
    organization_params_in_header,
]

contact_list_get_params = [
    organization_params_in_header,
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

contact_create_post_params = [
    organization_params_in_header,
    openapi.Parameter(
        "salutation", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "first_name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "last_name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "date_of_birth",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        format="date",
        example="2021-01-01",
    ),
    openapi.Parameter(
        "organization", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "title", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "primary_email", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "secondary_email", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "mobile_number", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "secondary_number", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "department", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "language", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "do_not_call", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter("address_line", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING),
    openapi.Parameter("street", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("state", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("pincode", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("country", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("description", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("linked_in_url", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("facebook_url", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("twitter_username", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("contact_attachment", openapi.IN_QUERY, type=openapi.TYPE_FILE),
]

contact_detail_get_params = [
    organization_params_in_header,
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
