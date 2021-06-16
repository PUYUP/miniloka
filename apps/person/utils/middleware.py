from rest_framework.response import Response


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_template_response(self, request, response):
        path = request.path
        if hasattr(response, 'data'):
            if 'token' in path and isinstance(response, Response):
                user = response.data.get('user')

                # role added
                user.update({'xxx': 'XXX'})
                response.data.update({'user': user})
        return response
