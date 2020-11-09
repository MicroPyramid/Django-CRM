from drf_yasg import openapi

company_params_in_header = openapi.Parameter(
    'company', openapi.IN_HEADER, required=True, type=openapi.TYPE_STRING)


account_list_get_params = [company_params_in_header]

account_list_post_params = [company_params_in_header]

account_create_get_params = [company_params_in_header]

account_create_post_params = [
    company_params_in_header,
    openapi.Parameter('name', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('phone', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('email', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_address_line', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_street', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_city', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_state', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_postcode', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_country', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('contacts', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
]


account_update_get_params = [company_params_in_header]

account_update_post_params = [
    company_params_in_header,
    openapi.Parameter('name', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('phone', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('email', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_address_line', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_street', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_city', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_state', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_postcode', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('billing_country', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
    openapi.Parameter('contacts', openapi.IN_QUERY,
                      required=True, type=openapi.TYPE_STRING),
]

account_delete_params = [
    company_params_in_header,
]
