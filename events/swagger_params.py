from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    "company", openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING
)

event_list_get_params = [
    company_params_in_header,
    openapi.Parameter(
        "name", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "created_by", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "assigned_users", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "date_of_meeting", openapi.IN_QUERY,
         type=openapi.FORMAT_DATE,
         example="2021-01-01"
    ),
]

event_detail_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "event_attachment", openapi.IN_QUERY, type=openapi.TYPE_FILE, 
    ),
    openapi.Parameter(
        "comment", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
]

event_delete_params = [
    company_params_in_header,
]

event_create_post_params = [
    company_params_in_header,
    openapi.Parameter(
        "name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "event_type", openapi.IN_QUERY, type=openapi.TYPE_STRING,
        required=True, enum=["Recurring","Non-Recurring"]
    ),
    openapi.Parameter(
        "contacts", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True,
    ),
    openapi.Parameter(
        "start_date", openapi.IN_QUERY,
         type=openapi.FORMAT_DATE, 
         example="2021-01-01"
    ),
    openapi.Parameter(
        "start_time", openapi.IN_QUERY,
         type=openapi.FORMAT_DATETIME,
         example="13:01:01"
    ),
    openapi.Parameter(
        "end_date", openapi.IN_QUERY,
         type=openapi.FORMAT_DATE,
         example="2021-01-01"
    ),
    openapi.Parameter(
        "end_time", openapi.IN_QUERY,
         type=openapi.FORMAT_DATETIME,
         example="13:01:01"
    ),
    openapi.Parameter(
        "teams", openapi.IN_QUERY, type=openapi.TYPE_STRING, 
    ),
    openapi.Parameter(
        "assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "description", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),  
    openapi.Parameter(
        "recurring_days", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),  
]

event_comment_edit_params = [
    company_params_in_header,
    openapi.Parameter(
        "comment", openapi.IN_QUERY, type=openapi.TYPE_STRING
    ),
]
