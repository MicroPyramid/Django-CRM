from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    "company", openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING
)


login_page_params = [
    company_params_in_header,
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
    company_params_in_header,
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

dashboard_params = [company_params_in_header]

user_update_params = [
    company_params_in_header,
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
    company_params_in_header,
    openapi.Parameter(
        "user_id", openapi.IN_QUERY, required=True, type=openapi.TYPE_NUMBER
    ),
]

check_sub_domain_params = [
    openapi.Parameter(
        "sub_domain", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
]

registration_page_params = [
    openapi.Parameter(
        "sub_domain", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
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
        "uidb64", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "token", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "new_password1", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        "new_password2", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    ),
]
user_list_params = [
    company_params_in_header,
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
    company_params_in_header,
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
    company_params_in_header,
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
    company_params_in_header,
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
    company_params_in_header,
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

settings_contact_create_params = [
    company_params_in_header,
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("last_name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("email", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

settings_contact_get_params = [
    company_params_in_header,
    openapi.Parameter("name", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("email", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("created_by", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

settings_blockdomains_create_params = [
    company_params_in_header,
    openapi.Parameter("domain", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

settings_blockemails_create_params = [
    company_params_in_header,
    openapi.Parameter("email", openapi.IN_QUERY, type=openapi.TYPE_STRING),
]

users_status_params = [
    company_params_in_header,
    openapi.Parameter(
        "status",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        enum=["Active", "Inactive"],
    ),
]
