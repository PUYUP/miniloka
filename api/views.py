# THIRD PARTY
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
                'verifycodes': reverse('person_api:verifycode-list', request=request,
                                       format=format, current_app='person'),
            },
            'core': {
                'csrf': reverse('core_api:csrf', request=request,
                                format=format, current_app='core'),
            },
        })
