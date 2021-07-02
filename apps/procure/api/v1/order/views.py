from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.generals import get_model
from .serializers import CreateOrderSerializer, RetrieveOrderSerializer

Order = get_model('procure', 'Order')


class OrderApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None

        self._queryset = Order.objects \
            .prefetch_related('user', 'propose', 'inquiry', 'offer') \
            .select_related('user', 'propose', 'inquiry', 'offer')

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        return super().dispatch(request, *args, **kwargs)

    def _instances(self):
        return self._queryset \
            .filter(inquiry__user_id=self.request.user.id)

    def _instance(self, is_update=False):
        try:
            if is_update:
                return self._instances().select_for_update() \
                    .get(uuid=self._uuid)
            else:
                return self._instances() \
                    .get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Not found"))
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))

    @transaction.atomic
    def create(self, request, format=None):
        serializer = CreateOrderSerializer(data=request.data, many=False,
                                           context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                return Response(
                    {'detail': _(" ".join(e.messages))},
                    status=response_status.HTTP_406_NOT_ACCEPTABLE
                )

            _serializer = RetrieveOrderSerializer(
                serializer.instance, many=False)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    def list(self, request, format=None):
        return Response('LIST', status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self._instance()
        serializer = RetrieveOrderSerializer(instance, many=False,
                                             context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
