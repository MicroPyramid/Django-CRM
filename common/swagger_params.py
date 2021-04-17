from drf_yasg import openapi

login_page_params = [
    openapi.Parameter(
        "email", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "password",
        openapi.IN_QUERY,
        format="password",
        required=True,
        type=openapi.TYPE_STRING,
    ),
]

change_password_params = [
    openapi.Parameter(
        "old_password",
        openapi.IN_QUERY,
        format="password",
        required=True,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        "new_password",
        openapi.IN_QUERY,
        format="password",
        required=True,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        "retype_password",
        openapi.IN_QUERY,
        format="password",
        required=True,
        type=openapi.TYPE_STRING,
    ),
]

user_update_params = [
    openapi.Parameter(
        "username", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        "first_name", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter("last_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("profile_pic", openapi.IN_QUERY, type=openapi.TYPE_FILE),
    openapi.Parameter("has_sales_access", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
    openapi.Parameter(
        "has_marketing_access", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

user_delete_params = [
    openapi.Parameter(
        "user_id", openapi.IN_QUERY, required=True, type=openapi.TYPE_NUMBER
    ),
]

registration_page_params = [
    openapi.Parameter(
        "username", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "email", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "password",
        openapi.IN_QUERY,
        format="password",
        required=True,
        type=openapi.TYPE_STRING,
    ),
]

forgot_password_params = [
    openapi.Parameter(
        "email", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
]

reset_password_params = [
    openapi.Parameter(
        "new_password1", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "new_password2", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
]

user_list_params = [
    openapi.Parameter("username", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("email", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "role", openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=["ADMIN", "USER"]
    ),
    openapi.Parameter(
        "status",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        enum=["Active", "In Active"],
    ),
]

user_create_params = [
    openapi.Parameter("username", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("email", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("role", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "password",
        openapi.IN_QUERY,
        format="password",
        required=True,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter("first_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("last_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("profile_pic", openapi.IN_QUERY, type=openapi.TYPE_FILE),
    openapi.Parameter("has_sales_access", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
    openapi.Parameter(
        "has_marketing_access", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter("status", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

document_create_params = [
    openapi.Parameter(
        "title", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        "document_file", openapi.IN_QUERY, type=openapi.TYPE_FILE, required=True
    ),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("shared_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

document_get_params = [
    openapi.Parameter("title", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "status",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        enum=["active", "inactive"],
    ),
    openapi.Parameter("shared_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

document_update_params = [
    openapi.Parameter(
        "title", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        "document_file", openapi.IN_QUERY, type=openapi.TYPE_FILE, required=True
    ),
    openapi.Parameter("teams", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("shared_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "status",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        enum=["active", "inactive"],
    ),
]

users_status_params = [
    openapi.Parameter(
        "status",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        enum=["Active", "Inactive"],
    ),
]

api_setting_create_params = [
    openapi.Parameter(
        "title", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter(
        "website", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    ),
    openapi.Parameter("lead_assigned_to", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter(
        "tags",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
    ),
]
