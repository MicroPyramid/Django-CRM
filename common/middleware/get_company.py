from common.models import Company


class GetCompany(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        company_id = request.session.get("company", None)
        if company_id:
            company = Company.objects.get(id=company_id)
            request.company = company
            request.session["company"] = company.id
        else:
            host_name = request.META.get("HTTP_HOST")
            subdomain = host_name.split(".")[0]
            company = Company.objects.filter(sub_domain=subdomain).first()
            if company:
                request.company = company
                request.session["company"] = company.id
