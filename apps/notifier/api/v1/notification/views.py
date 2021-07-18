from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Count, Q, F, Subquery, OuterRef, Case, When

from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import NotificationSerializer

Notification = get_model('notifier', 'Notification')
Offer = get_model('procure', 'Offer')
Inquiry = get_model('procure', 'Inquiry')
Listing = get_model('procure', 'Listing')
Order = get_model('procure', 'Order')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class NotificationApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None

        self._queryset = Notification.objects \
            .prefetch_related('recipient', 'actor_content_type', 'actor',
                              'target_content_type', 'target',
                              'action_object_content_type', 'action_object') \
            .select_related('recipient', 'actor_content_type',
                            'target_content_type', 'action_object_content_type')

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        return super().dispatch(request, *args, **kwargs)

    def _instances(self):
        offer = Offer.objects \
            .select_related('propose') \
            .prefetch_related('propose') \
            .filter(id=OuterRef('action_object_object_id'))

        offer_target = Offer.objects \
            .select_related('propose') \
            .prefetch_related('propose') \
            .filter(id=OuterRef('target_object_id'))

        inquiry = Inquiry.objects \
            .filter(id=OuterRef('action_object_object_id'))

        listing = Listing.objects \
            .select_related('members') \
            .prefetch_related('members') \
            .filter(
                id=OuterRef('target_object_id'),
                members__is_default=True,
                members__user_id=self.request.user.id
            )

        order = Order.objects \
            .filter(id=OuterRef('action_object_object_id'))

        return self._queryset \
            .annotate(
                action_object_uuid=Case(
                    When(
                        action_object_content_type__model='offer',
                        then=Subquery(offer.values('propose__uuid')[:1])
                    ),
                    When(
                        action_object_content_type__model='inquiry',
                        then=Subquery(inquiry.values('uuid')[:1])
                    ),
                    When(
                        action_object_content_type__model='order',
                        then=Subquery(order.values('uuid')[:1])
                    ),
                ),
                target_uuid=Case(
                    When(
                        target_content_type__model='listing',
                        then=Subquery(listing.values('uuid')[:1])
                    ),
                    When(
                        target_content_type__model='offer',
                        then=Subquery(offer_target.values('uuid')[:1])
                    ),
                )
            ) \
            .filter(recipient_id=self.request.user.id, unread=True)

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

    def list(self, request, format=None):
        instances = self._instances()
        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = NotificationSerializer(paginator, context=self._context,
                                            many=True)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_name='recaps', url_path='recaps',
            permission_classes=(IsAuthenticated,))
    def recaps(self, request, uuid=None, format=None):
        newest_offer = Offer.objects \
            .filter(is_newest=True, id=OuterRef('action_object_object_id'))

        notification = Notification.objects \
            .filter(recipient_id=request.user.id) \
            .annotate(newest_offer_id=Subquery(newest_offer.values('id')[:1])) \
            .aggregate(
                total=Count('id'),
                total_unread=Count('id', filter=Q(unread=True)),
                total_read=Count('id', filter=Q(unread=False)),

                unread_inquiry=Count(
                    'target_object_id',
                    filter=Q(target_content_type__model='listing')
                    & Q(action_object_content_type__model='inquiry')
                    & Q(unread=True)
                ),

                unread_offer=Count(
                    'action_object_object_id',
                    filter=Q(target_content_type__model='inquiry')
                    & Q(action_object_content_type__model='offer')
                    & Q(newest_offer_id=F('action_object_object_id'))
                    & Q(unread=True)
                )
            )

        return Response(notification, status=response_status.HTTP_200_OK)

    # Mark read
    @action(methods=['POST'], detail=True, url_name='mark_read', url_path='mark-read',
            permission_classes=(IsAuthenticated,))
    def mark_read(self, request, uuid=None, format=None):
        instance = self._instance()
        instance.mark_as_read()
        return Response({'detail': _("Success!")}, status=response_status.HTTP_200_OK)

    # Mark unread
    @action(methods=['POST'], detail=True, url_name='mark_unread', url_path='mark-unread',
            permission_classes=(IsAuthenticated,))
    def mark_unread(self, request, uuid=None, format=None):
        instance = self._instance()
        instance.mark_as_unread()
        return Response({'detail': _("Success!")}, status=response_status.HTTP_200_OK)

    # Mark all read
    @action(methods=['POST'], detail=False, url_name='mark_all_read', url_path='mark-all-read',
            permission_classes=(IsAuthenticated,))
    def mark_all_read(self, request, uuid=None, format=None):
        Notification.objects.mark_all_as_read(recipient=request.user)
        return Response({'detail': _("Success!")}, status=response_status.HTTP_200_OK)
