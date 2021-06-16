from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.decorators import action

from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import ListOfferSerializer, RetrieveOfferSerializer

Offer = get_model('procure', 'Offer')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class OfferApiView(viewsets.ViewSet):
    """
    ## GET Attribute;
    --------
        [*] offer_uuid      : uuid v4
        Offer in offer  : ./?offer_uuid=255640d0-c552-49e9-a0e5-c40b63ce0a1f
    """

    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None
        self._queryset = Offer.objects \
            .prefetch_related('items', 'items__inquiry_item', 'propose', 'user') \
            .select_related('propose', 'user')

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        return super().dispatch(request, *args, **kwargs)

    def _instances(self):
        # Get offer cost by inquiry creator
        return self._queryset.filter(Q(propose__inquiry__user_id=self.request.user.id)
                                     | Q(user_id=self.request.user.id))

    def _instance(self, is_update=False):
        try:
            if is_update:
                return self._instances() \
                    .select_for_update() \
                    .get(uuid=self._uuid)
            else:
                return self._instances() \
                    .get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Not found"))
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))

    def list(self, request, format='json'):
        instances = self._instances()
        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = ListOfferSerializer(paginator, context=self._context,
                                         many=True)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format='json'):
        instance = self._instance()
        serializer = RetrieveOfferSerializer(instance, many=False,
                                             context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_name='offer-items', url_path='items',
            permission_classes=(IsAuthenticated,))
    def items(self, request, uuid=None, format='json'):
        pass
