from django.db import transaction, IntegrityError
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import (
    Q, F, Sum, IntegerField, Case, When, Value, BooleanField,
    DecimalField, Count
)
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
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

from utils.mixin.viewsets import ViewSetDestroyObjMixin
from utils.validators import csrf_protect_drf
from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import (
    CreateOfferSerializer,
    ListOfferSerializer,
    RetrieveOfferSerializer,
    RetrieveOfferSerializer
)

Need = get_model('servo', 'Need')
Offer = get_model('servo', 'Offer')
OfferRate = get_model('servo', 'OfferRate')
OfferItem = get_model('servo', 'OfferItem')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


@method_decorator([ensure_csrf_cookie, csrf_protect_drf], name='dispatch')
class OfferApiView(ViewSetDestroyObjMixin, viewsets.ViewSet):
    """
    # POST Param;
    --------
        [*] if never offer, create new
        [*] if offered, update offer and insert new offer_rates

        {
            "need": "3ed5697e-a031-4ab5-b99f-d6fb0084b51b",     [required]
            "rates": {                                          [required]
                "cost": 4100,
                "description": "Lllllf al"
            }
        }


    # GET Attribute;
    --------
        [*] only need creator and user can see results
        [*] need_uuid   : uuid v4

        Offer in need   : ./?need_uuid=255640d0-c552-49e9-a0e5-c40b63ce0a1f
    """

    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None
        self._user = None

        self._queryset = Offer.objects \
            .prefetch_related('listing', 'need', 'rates', 'rates__offeror') \
            .select_related('listing', 'need')

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        self._user = request.user
        return super().dispatch(request, *args, **kwargs)

    def _get_instances(self, order_param=dict()):
        offer_order_bys = list()
        passed_fields = ('cost', 'distance',)
        whole_rate_filter = Q(items__item_rates__is_newest=True)
        whole_rate_sum = When(
            items__item_rates__isnull=False,
            then=Sum(
                'items__item_rates__cost',
                filter=whole_rate_filter,
                output_field=IntegerField()
            ),
        )

        try:
            rates = OfferRate.objects \
                .filter(offer_id=OuterRef('id')) \
                .values('offer')
        except FieldError as e:
            raise ValidationError({'detail': str(e)})

        # Calculate distance
        _query_distance = Value(3959) * ACos(
            Cos(Radians(F('rate_latitude'), output_field=DecimalField()))
            * Cos(Radians(F('need_latitude'), output_field=DecimalField()))
            * Cos(Radians(F('need_longitude'), output_field=DecimalField()))
            - Radians(F('rate_longitude'), output_field=DecimalField())
            + Sin(Radians(F('rate_latitude'), output_field=DecimalField()))
            * Sin(Radians(F('need_latitude'), output_field=DecimalField())),
            output_field=DecimalField()
        )

        # Default annotate
        annotate = {
            'rate_latitude': Subquery(rates.values('latitude')[:1]),
            'rate_longitude': Subquery(rates.values('longitude')[:1]),
            'need_latitude': Coalesce(
                F('need__location__latitude'),
                Value(0),
                output_field=DecimalField()
            ),
            'need_longitude': Coalesce(
                F('need__location__longitude'),
                Value(0),
                output_field=DecimalField()
            ),
            'rate_distance': _query_distance,
            'rate_cost': Case(
                whole_rate_sum,
                default=Subquery(rates.values('cost')[:1]),
                output_field=IntegerField()
            ),
            'rate_create_at': Subquery(rates.values('create_at')[:1])
        }

        if order_param:
            # make sure order_param has passed_fields
            n = {k: order_param[k] for k in passed_fields if k in order_param}
            if n:
                for key in n:
                    l = 'rate_%s' % key
                    direction = n.get(key, None)
                    if direction == 'desc':
                        l = '-%s' % l  # rate_cost to -rate_cost
                        key = '-%s' % key  # cost to -cost
                    offer_order_bys.append(l)
        else:
            # default order...
            offer_order_bys = ('-rate_create_at', '-rate_distance',)

        # Whole rate?
        annotate.update({
            'is_whole_rate': Case(
                When(
                    items__item_rates__isnull=False,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        })

        return self._queryset \
            .filter(Q(need__user_id=self._user.id)
                    | Q(listing__members__user_id=self._user.id)) \
            .annotate(count_listing=Count('listing'), **annotate) \
            .order_by(*offer_order_bys)

    def _get_instance(self, is_update=False):
        try:
            if is_update:
                return self._get_instances() \
                    .select_for_update() \
                    .get(uuid=self._uuid)
            else:
                return self._get_instances() \
                    .annotate() \
                    .prefetch_related('items', 'items__item_rates',
                                      'items__item_rates__offer_item',
                                      'items__item_rates__offer_item__needitem') \
                    .get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Not found"))
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))

    def list(self, request, format='json'):
        params = {k: v for k, v in request.query_params.items() if v}
        need_uuid = params.get('need_uuid', None)

        order_param = dict()
        order = params.get('order', None)
        order_list = order.split(',') if order else list()
        for query in order_list:
            query_matcher = query.split(' ') or query.split('+')
            try:
                order_param.update({query_matcher[0]: query_matcher[1]})
            except:
                pass

        instances = self._get_instances(order_param=order_param)
        if need_uuid:
            try:
                instances = instances.filter(need__uuid=need_uuid)
            except ValidationError as e:
                raise ValidationError(str(e))

        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = ListOfferSerializer(paginator, context=self._context,
                                         many=True)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format='json'):
        instance = self._get_instance()
        serializer = RetrieveOfferSerializer(instance, many=False,
                                             context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @ transaction.atomic()
    def create(self, request, format='json'):
        serializer = CreateOfferSerializer(data=request.data,
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

            _serializer = RetrieveOfferSerializer(serializer.instance, many=False,
                                                  context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @ transaction.atomic()
    def partial_update(self, request, uuid=None, format='json'):
        instance = self._get_instance()
        serializer = CreateOfferSerializer(instance, partial=True, many=False,
                                           data=request.data, context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
