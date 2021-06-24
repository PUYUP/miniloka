from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action

from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import (
    CreateListingMemberSerializer,
    CreateListingOpeningSerializer,
    CreateListingSerializer,
    ListListingSerializer,
    RetrieveListingMemberSerializer,
    RetrieveListingOpeningSerializer,
    RetrieveListingSerializer,
    RetrieveListingLocationSerializer,
    UpdateListingLocationSerializer
)

Listing = get_model('procure', 'Listing')
ListingMember = get_model('procure', 'ListingMember')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class ListingApiView(viewsets.ViewSet):
    """
    POST Params;
    --------
        {
            "label": "string",                      [required]
            "description": "string"                 [optional]
        }

    GET Attribute;
    --------
        [*] results all listings submited
    """

    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None
        self._queryset = Listing.objects \
            .prefetch_related('location', 'state', 'members', 'openings') \
            .select_related('location', 'state')

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        return super().dispatch(request, *args, **kwargs)

    def _instances(self):
        return self._queryset.filter(members__user_id=self.request.user.id) \
            .order_by('-create_at')

    def _instance(self, is_update=False):
        try:
            if is_update:
                return self._instances().select_for_update() \
                    .get(uuid=self._uuid, members__is_admin=True)
            else:
                return self._instances().get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Not found"))
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))

    def list(self, request, format='json'):
        instances = self._instances()
        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = ListListingSerializer(paginator, context=self._context,
                                           many=True)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format='json'):
        instance = self._instance()
        serializer = RetrieveListingSerializer(instance, many=False,
                                               context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic()
    def create(self, request, format='json'):
        serializer = CreateListingSerializer(data=request.data,
                                             context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response(
                    {'detail': _(" ".join(e.messages))},
                    status=response_status.HTTP_406_NOT_ACCEPTABLE
                )

            _serializer = RetrieveListingSerializer(serializer.instance,
                                                    context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @transaction.atomic()
    def partial_update(self, request, uuid=None, format='json'):
        instance = self._instance(is_update=True)
        serializer = CreateListingSerializer(instance, partial=True, many=False,
                                             data=request.data, context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response(
                    {'detail': _(" ".join(e.messages))},
                    status=response_status.HTTP_406_NOT_ACCEPTABLE
                )

            _serializer = RetrieveListingSerializer(serializer.instance,
                                                    context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @transaction.atomic()
    def delete(self, request, uuid=None):
        instances = self._instances() \
            .filter(uuid=self._uuid, members__is_admin=True)

        if instances.exists():
            instances.delete()
            return Response(
                {'detail': _("Delete success")},
                status=response_status.HTTP_200_OK
            )
        raise NotFound()

    # LOCATION
    @transaction.atomic
    @action(methods=['patch'], detail=True, url_path='location', url_name='location')
    def location(self, request, uuid=None, format='json'):
        """
        Format;
        ---------
            {
                "street_address": "string",                 [required]
                "administrative_area_level_1": "string (province)", [required]
                "administrative_area_level_2": "string (city)",     [required]
                "administrative_area_level_3": "string (district)", [required]
                "administrative_area_level_4": "string (village)",  [required]
                "postal_code": "string",                    [required]
                "latitude": "decimal",                      [required]
                "longitude": "decimal"                      [required]
            }
        """
        instance = self._instance(is_update=True)
        serializer = UpdateListingLocationSerializer(instance.location,
                                                     data=request.data,
                                                     context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            _serializer = RetrieveListingLocationSerializer(serializer.instance,
                                                            context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # OPENINGS
    @transaction.atomic
    @action(methods=['put'], detail=True, url_path='openings', url_name='opening')
    def openings(self, request, uuid=None, format='json'):
        """
        PUT
        -----------

        Format;

            [
                {"day": 1, "open_time": "12:00", "close_time": "17:00", "uuid": "0f50f4fb-9ce5-45ec-a588-0c271a1f32f1"},                    [update]
                {"day": 2, "open_time": "12:00", "close_time": "17:00", "uuid": "0f50f4fb-9ce5-45ec-a588-0c271a1f32f1", "is_delete": true}, [delete]
                {"day": 3, "open_time": "14:00", "close_time": "10:00"}                                                                     [create]
            ]

        Rules;

            * If opening with day exist will update only
            * Used method update_or_create()
        """

        instance = self._instance()
        self._context.update({'listing': instance})
        serializer = CreateListingOpeningSerializer(instance=instance.openings.all(),
                                                    data=request.data, partial=False,
                                                    many=True, context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            _serializer = RetrieveListingOpeningSerializer(
                serializer.instance, many=True, context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # MEMBERS
    @transaction.atomic
    @action(methods=['post'], detail=True, url_path='members', url_name='member')
    def members(self, request, uuid=None, format='json'):
        """
        POST
        ------------

        Format;

            {
                "user": "user email",
                "is_admin": false,
                "is_allow_propose": false
            }
        """
        instance = self._instance()
        self._context.update({'listing': instance})

        serializer = CreateListingMemberSerializer(data=request.data, many=False,
                                                   context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            _serializer = RetrieveListingMemberSerializer(serializer.instance, many=False,
                                                          context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    @action(methods=['patch'], detail=True,
            url_path='members/(?P<member_uuid>[^/.]+)', url_name='member_update')
    def members_update(self, request, uuid=None, member_uuid=None, format='json'):
        pass

    @transaction.atomic
    @action(methods=['post'], detail=True,
            url_path='set-default', url_name='set_default')
    def set_default(self, request, uuid=None, format='json'):
        user_id = request.user.id

        try:
            member = ListingMember.objects \
                .get(user_id=user_id, listing__uuid=uuid, is_default=False)
            member.is_default = True
            member.save(update_fields=['is_default'])
        except ObjectDoesNotExist:
            pass

        return Response({'detail': _("Success")}, status=response_status.HTTP_200_OK)
