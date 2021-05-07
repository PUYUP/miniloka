from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'ping': reverse('ping', request=request, format=format),
            'person': {
                'token': reverse('person_api:token_obtain_pair', request=request,
                                 format=format, current_app='person'),
                'token-refresh': reverse('person_api:token_refresh', request=request,
                                         format=format, current_app='person'),
                'users': reverse('person_api:user-list', request=request,
                                 format=format, current_app='person'),
                'verifycodes': reverse('person_api:verifycode-list', request=request,
                                       format=format, current_app='person'),
            },
            'servo': {
                'customer': {
                    'needs': reverse('servo_api:customer:need-list', request=request,
                                     format=format, current_app='servo'),
                    'offers': reverse('servo_api:customer:offer-list', request=request,
                                      format=format, current_app='servo'),
                    'offer-rates': reverse('servo_api:customer:offer_rate-list', request=request,
                                           format=format, current_app='servo'),
                },
                'owner': {
                    'listings': reverse('servo_api:owner:listing-list', request=request,
                                        format=format, current_app='servo'),
                }
            }
        })


@api_view(['GET'])
@permission_classes((AllowAny, ))
@ensure_csrf_cookie
def ping(request):
    csrftoken = request.COOKIES.get('csrftoken')
    if not csrftoken:
        raise NotFound(detail=_("CSRF Token not set"))
    return Response({'csrftoken': csrftoken})
