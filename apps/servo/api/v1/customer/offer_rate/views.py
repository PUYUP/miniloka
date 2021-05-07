from utils.mixin.viewsets import ViewSetDestroyObjMixin, ViewSetGetObjMixin
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.validators import csrf_protect_drf
from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import OfferRateSerializer

OfferRate = get_model('servo', 'OfferRate')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


@method_decorator([ensure_csrf_cookie, csrf_protect_drf], name='dispatch')
class OfferRateApiView(ViewSetGetObjMixin, ViewSetDestroyObjMixin,
                       viewsets.ViewSet):
    """
    ## GET Attribute;
    --------
        [*] offer_uuid      : uuid v4
        OfferRate in offer  : ./?offer_uuid=255640d0-c552-49e9-a0e5-c40b63ce0a1f
    """

    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None
        self._user = None
        self._queryset = OfferRate.objects.prefetch_related('offer', 'offer__need') \
            .select_related('offer', 'offer__need')

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        self._user = request.user
        return super().dispatch(request, *args, **kwargs)

    def _get_instances(self):
        # Get offer cost by need creator
        return self._queryset.filter(offer__need__user_id=self._user.id)

    def list(self, request, format='json'):
        params = {k: v for k, v in request.query_params.items() if v}
        offer_uuid = params.get('offer_uuid', None)
        instances = self._get_instances()
        if offer_uuid:
            instances = instances.filter(offer__uuid=offer_uuid)
        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = OfferRateSerializer(paginator, context=self._context,
                                         many=True)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format='json'):
        instance = self._get_instance()
        serializer = OfferRateSerializer(instance, many=False,
                                         context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
