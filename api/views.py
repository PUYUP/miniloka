from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'person': {
                'token': reverse('person_api:token_obtain_pair', request=request,
                                 format=format, current_app='person'),
                'token-refresh': reverse('person_api:token_refresh', request=request,
                                         format=format, current_app='person'),
                'users': reverse('person_api:user-list', request=request,
                                 format=format, current_app='person'),
                'securecodes': reverse('person_api:securecode-list', request=request,
                                       format=format, current_app='person'),
            },
            'procure': {
                'inquiries': reverse('procure_api:inquiry-list', request=request,
                                     format=format, current_app='procure'),
                'proposes': reverse('procure_api:propose-list', request=request,
                                    format=format, current_app='procure'),
                'offers': reverse('procure_api:offer-list', request=request,
                                  format=format, current_app='procure'),
                'listings': reverse('procure_api:listing-list', request=request,
                                    format=format, current_app='procure'),
                'orders': reverse('procure_api:order-list', request=request,
                                  format=format, current_app='procure'),
                'products': reverse('procure_api:product-list', request=request,
                                    format=format, current_app='procure'),
            }
        })
