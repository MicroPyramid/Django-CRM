import json


class SwaggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        request.body  # just add this line BEFORE get_response

        request.post_data = (
            request.GET if len(request.POST) == 0 else request.POST
        )  # for swagger

        if request.post_data == {} and request.body:  # <--- for raw data (import)
            request.post_data = json.loads(request.body)

        response = self.get_response(request)
        return response
