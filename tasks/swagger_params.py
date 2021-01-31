from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    "company", openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING
)

task_list_get_params = [
    company_params_in_header,
    openapi.Parameter(
        "title", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "status", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "priority", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
]

task_detail_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "task_attachment", openapi.IN_QUERY, type=openapi.TYPE_FILE, 
    ),
    openapi.Parameter(
        "comment", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
]

task_delete_params = [
    company_params_in_header,
]

task_create_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "title", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "status", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "priority", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "due_date", openapi.IN_QUERY,
         type=openapi.FORMAT_DATE,
         example="2021-01-01"
    ),
    openapi.Parameter(
        "account", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "contacts", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "teams", openapi.IN_QUERY, type=openapi.TYPE_STRING, 
    ),
    openapi.Parameter(
        "assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
]

task_comment_edit_params = [
    company_params_in_header,
    openapi.Parameter(
        "comment", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
]
