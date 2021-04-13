from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions


class CsrfTokenApiView(APIView):
    """
    Generate CSRFtoken
    """
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, format=None):
        csrftoken = request.COOKIES.get('csrftoken')
        if not csrftoken:
            raise NotFound(detail=_("CSRF Token not set"))
        return Response({'csrftoken': csrftoken})
