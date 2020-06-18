from common.models import Company
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class GetCompany(object):
    """adding company to request object
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)

        return response

    def process_request(self, request):
        company = request.session.get("company", None)
        if company:
            company = Company.objects.filter(id=company).first()
            if company:
                request.company = company

        else:
            domain = settings.DOMAIN_NAME
            login_url = request.scheme + "://" + domain + reverse("login")
            host_name = request.META.get("HTTP_HOST")

            if host_name:
                subdomain = host_name.split(".")[0]
                if subdomain == "" or subdomain == "api":
                    request.company = ""
                else:
                    company = Company.objects.filter(sub_domain=subdomain).first()
                    if company:
                        request.company = company
                        if request.user.is_authenticated:

                            if request.company != request.user.company:
                                logout(request)
                                return redirect(login_url)
                    else:
                        logout(request)
                        return redirect(login_url)
