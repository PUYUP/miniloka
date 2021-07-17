from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models.expressions import Case, Value, When
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, F, Sum, IntegerField

from rest_framework import status as response_status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.generals import get_model
from .serializers import CreateOrderSerializer, RetrieveOrderSerializer

Order = get_model('procure', 'Order')
Submission = get_model('peerland', 'Submission')


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
            .annotate(
                is_creator=Case(
                    When(inquiry__user_id=self.request.user.id, then=Value(True)),
                    default=Value(False)
                ),
                total_item_cost=Sum('items__cost'),
                total_cost=Case(
                    When(cost__lte=0, then=F('total_item_cost')),
                    default=F('cost'),
                    output_field=IntegerField()
                )
            ) \
            .filter(
                Q(inquiry__user_id=self.request.user.id)
                | Q(offer__user_id=self.request.user.id)
            )

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
            error_message = None

            try:
                serializer.save()
            except DjangoValidationError as e:
                error_message = _(" ".join(e.messages))
            except IntegrityError as e:
                error_message = str(e)

            if error_message is not None:
                return Response(
                    {'detail': error_message},
                    status=response_status.HTTP_406_NOT_ACCEPTABLE
                )

            _serializer = RetrieveOrderSerializer(serializer.instance,
                                                  many=False)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @transaction.atomic()
    def delete(self, request, uuid=None):
        instances = self._instances() \
            .filter(uuid=self._uuid, user_id=request.user.id)

        if instances.exists():
            # check has Submission
            instance = instances.get()
            submission = Submission.objects \
                .filter(burden_content_type__model='order', burden_object_id=instance.id,
                        status=Submission.Status.APPROVED)

            if submission.exists():
                raise ValidationError(
                    detail=_("Sedang dicicil tidak bisa dibatalkan.")
                )

            instances.delete()
            return Response(
                {'detail': _("Delete success")},
                status=response_status.HTTP_200_OK
            )
        raise NotFound()

    def list(self, request, format=None):
        return Response('LIST', status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self._instance()
        serializer = RetrieveOrderSerializer(instance, many=False,
                                             context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
