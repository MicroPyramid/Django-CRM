from drf_yasg import openapi

organization_params_in_header = openapi.Parameter(
    "org", openapi.IN_HEADER, required=True, type=openapi.TYPE_INTEGER
)

organization_params = [
    organization_params_in_header,
]

account_get_params = [
    organization_params_in_header,
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("city", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("tags", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

account_post_params = [
    organization_params_in_header,
    openapi.Parameter(
        "name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "phone", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "email", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "billing_address_line",
        openapi.IN_QUERY,
        required=True,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        "billing_street", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "billing_city", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "billing_state", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "billing_postcode", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "billing_country", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "contacts", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "tags",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING
        # type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)
    ),
    openapi.Parameter("account_attachment", openapi.IN_QUERY, type=openapi.TYPE_FILE),
    openapi.Parameter("website", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "status", openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=["open", "close"]
    ),
    openapi.Parameter("lead", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

account_detail_get_params = [
    organization_params_in_header,
    openapi.Parameter(
        "account_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

account_comment_edit_params = [
    organization_params_in_header,
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

account_detail_get_params = [
    organization_params_in_header,
    openapi.Parameter(
        "account_attachment",
        openapi.IN_QUERY,
        type=openapi.TYPE_FILE,
    ),
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

account_comment_edit_params = [
    organization_params_in_header,
    openapi.Parameter("comment", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

account_mail_params = [
    organization_params_in_header,
    openapi.Parameter("from_email", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("recipients", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("message_subject", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("scheduled_later", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
    openapi.Parameter("timezone", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "scheduled_date_time",
        openapi.IN_QUERY,
        type=openapi.FORMAT_DATETIME,
        example="2021-01-01 00:00",
    ),
    openapi.Parameter("message_body", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]
