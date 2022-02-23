from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    "org", openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING
)

invoice_list_get_params = [
    company_params_in_header,
    openapi.Parameter(
        "invoice_title_or_number", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("created_by", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("assigned_users", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("status", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("total_amount", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

invoice_detail_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "invoice_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

invoice_delete_params = [
    company_params_in_header,
]

invoice_create_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "invoice_title", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("status", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("from_address_line", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("from_street", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("from_city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("from_state", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("from_postcode", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("from_country", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("to_address_line", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("to_street", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("to_city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("to_state", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("to_postcode", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("to_country", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "email", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("phone", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "due_date", openapi.IN_QUERY, type=openapi.FORMAT_DATE, example="2021-02-28"
    ),
    openapi.Parameter(
        "currency", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("accounts", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("quality_hours", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("rate", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("tax", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("total_amount", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("details", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

invoice_comment_edit_params = [
    company_params_in_header,
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]
