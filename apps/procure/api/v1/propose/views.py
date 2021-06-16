from django.db import transaction, IntegrityError
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import (
    Q, F, Sum, IntegerField, Case, When, Value, BooleanField,
    FloatField, Count
)
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import (
    FieldError,
    ObjectDoesNotExist,
    ValidationError as DjangoValidationError
)

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action

from utils.mixin.viewsets import ViewSetDestroyObjMixin
from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import (
    CreateProposeSerializer,
    ListProposeSerializer,
    RetrieveProposeSerializer,
    RetrieveProposeSerializer
)
from ..offer.serializers import ListOfferSerializer

Inquiry = get_model('procure', 'Inquiry')
Propose = get_model('procure', 'Propose')
Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class ProposeApiView(ViewSetDestroyObjMixin, viewsets.ViewSet):
    """
    ## POST Param;
    --------
        [*] create if not exist and update if exist
        [*] 'offer' indicate offer to all items and set 'offer_items->cost' to 0

        {
            "listing": "uuid",              [required]
            "inquiry": "uuid",              [required]
            "coordinate": {                 [required]
                "latitude": "float",
                "longitude": "float"
            },
            "offer": {                      [optional]
                "cost": "integer"
            },                                     
            "offer_items": [                [required]
                {                                             
                    "inquiry_item": "uuid",
                    "cost": "integer"
                }
            ]
        }

    ----------
    ### Example
    ----------

        {
            "listing": "ee5ae6db-32ba-4c32-afa9-b11a5e1782b2",
            "inquiry": "ee5ae6db-32ba-4c32-afa9-b11a5e1782b2",
            "coordinate": {
                "latitude": 10.0, 
                "longitude": 0.2
            },
            "offer": {
                "cost": 9000
            },
            "offer_items": [
                {"cost": 13, "inquiry_item": "3e773651-335a-49bc-9f46-03e468c8dadd"}
            ]
        }


    --------
    ## GET Attribute;
    --------
        [*] only inquiry creator and user can see results
        [*] inquiry_uuid   : uuid v4

        Propose in inquiry   : ./?inquiry_uuid=255640d0-c552-49e9-a0e5-c40b63ce0a1f
    """

    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None

        self._queryset = Propose.objects \
            .prefetch_related('listing', 'inquiry', 'offers', 'offers__user') \
            .select_related('listing', 'inquiry')

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        return super().dispatch(request, *args, **kwargs)

    def _instances(self, order_param=dict()):
        offer_order_bys = list()
        passed_fields = ('cost', 'distance',)
        whole_cost_filter = Q(offers__items__is_newest=True)
        whole_cost_sum = When(
            offers__items__isnull=False,
            then=Sum(
                'offers__items__cost',
                filter=whole_cost_filter,
                output_field=IntegerField()
            ),
        )

        try:
            offers = Offer.objects \
                .filter(propose_id=OuterRef('id')) \
                .values('propose')
        except FieldError as e:
            raise ValidationError({'detail': str(e)})

        # Calculate distance
        _query_distance = Value(3959) * ACos(
            Cos(Radians(F('offer_latitude'), output_field=FloatField()))
            * Cos(Radians(F('inquiry_latitude'), output_field=FloatField()))
            * Cos(Radians(F('inquiry_longitude'), output_field=FloatField())
                  - Radians(F('offer_longitude'), output_field=FloatField()))
            + Sin(Radians(F('offer_latitude'), output_field=FloatField()))
            * Sin(Radians(F('inquiry_latitude'), output_field=FloatField())),
            output_field=FloatField()
        )

        # Default annotate
        annotate = {
            'offer_latitude': Subquery(offers.values('latitude')[:1]),
            'offer_longitude': Subquery(offers.values('longitude')[:1]),
            'inquiry_latitude': Coalesce(
                F('inquiry__location__latitude'),
                Value(0),
                output_field=FloatField()
            ),
            'inquiry_longitude': Coalesce(
                F('inquiry__location__longitude'),
                Value(0),
                output_field=FloatField()
            ),
            'offer_distance': _query_distance,
            'offer_cost': Case(
                whole_cost_sum,
                default=Subquery(offers.values('cost')[:1]),
                output_field=IntegerField()
            ),
            'offer_create_at': Subquery(offers.values('create_at')[:1])
        }

        if order_param:
            # make sure order_param has passed_fields
            n = {k: order_param[k] for k in passed_fields if k in order_param}
            if n:
                for key in n:
                    l = 'offer_%s' % key
                    direction = n.get(key, None)
                    if direction == 'desc':
                        l = '-%s' % l  # 'offer_cost' to '-offer_cost'
                        key = '-%s' % key  # 'cost' to '-cost'
                    offer_order_bys.append(l)
        else:
            # default order...
            offer_order_bys = ('-offer_create_at', '-offer_distance',)

        # Whole offer?
        # If each propose item has rates mark as whole offer
        annotate.update({
            'is_whole_offer': Case(
                When(
                    offers__items__isnull=False,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        })

        return self._queryset \
            .filter(Q(inquiry__user_id=self.request.user.id)
                    | Q(listing__members__user_id=self.request.user.id)) \
            .annotate(count_listing=Count('listing'), **annotate) \
            .order_by(*offer_order_bys)

    def _instance(self, is_update=False):
        try:
            if is_update:
                return self._instances() \
                    .select_for_update() \
                    .get(uuid=self._uuid)
            else:
                return self._instances() \
                    .prefetch_related('offers', 'offers__items') \
                    .get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Not found"))
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))

    @transaction.atomic()
    def create(self, request, format='json'):
        serializer = CreateProposeSerializer(data=request.data,
                                             context=self._context)
        if serializer.is_valid(raise_exception=True):
            _error = None

            try:
                serializer.save()
            except IntegrityError as e:
                _error = str(e)
            except DjangoValidationError as e:
                _error = str(e)
            except ValidationError as e:
                _error = str(e)

            if _error is not None:
                return Response({'detail': _error}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            _serializer = RetrieveProposeSerializer(serializer.instance, many=False,
                                                    context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @transaction.atomic()
    def partial_update(self, request, uuid=None, format='json'):
        instance = self._instance()
        serializer = CreateProposeSerializer(instance, partial=True, many=False,
                                             data=request.data, context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """
    All proposes
    """

    def list(self, request, format='json'):
        params = {k: v for k, v in request.query_params.items() if v}
        inquiry_uuid = params.get('inquiry_uuid', None)

        order_param = dict()
        order = params.get('order', None)
        order_list = order.split(',') if order else list()
        for query in order_list:
            query_matcher = query.split(' ') or query.split('+')
            try:
                order_param.update({query_matcher[0]: query_matcher[1]})
            except:
                pass

        instances = self._instances(order_param=order_param)
        if inquiry_uuid:
            try:
                instances = instances.filter(inquiry__uuid=inquiry_uuid)
            except ValidationError as e:
                raise ValidationError(str(e))

        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = ListProposeSerializer(paginator, context=self._context,
                                           many=True)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    """
    A single
    """

    def retrieve(self, request, uuid=None, format='json'):
        instance = self._instance()
        serializer = RetrieveProposeSerializer(instance, many=False,
                                               context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    """
    Get offers
    """

    @action(methods=['GET'], detail=True, url_name='offers', url_path='offers',
            permission_classes=(IsAuthenticated,))
    def offers(self, request, uuid=None, format='json'):
        offers = Offer.objects \
            .prefetch_related('user', 'propose') \
            .select_related('user', 'propose') \
            .filter(propose__uuid=uuid)

        paginator = _PAGINATOR.paginate_queryset(offers, request)
        serializer = ListOfferSerializer(paginator, many=True,
                                         context=self._context)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)
