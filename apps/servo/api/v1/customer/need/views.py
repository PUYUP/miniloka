from utils.mixin.viewsets import ViewSetDestroyObjMixin, ViewSetGetObjMixin
from django.db import transaction
from django.db.models import Prefetch, Count
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination

from utils.validators import csrf_protect_drf
from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import CreateNeedSerializer, ListNeedSerializer, RetrieveNeedSerializer

Need = get_model('servo', 'Need')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


@method_decorator([ensure_csrf_cookie, csrf_protect_drf], name='dispatch')
class NeedApiView(ViewSetGetObjMixin, ViewSetDestroyObjMixin,
                  viewsets.ViewSet):
    """
    POST Params;
    --------
        [*] variety (one of: repair, looking, buying)

        {
            "description": "string",                [optional]
            "variety": "string",                    [required]
            "location": {                           [required]
                "latitude": "float",
                "longiteu": "float"
            },
            "items": [                              [optional]
                {"label": "string"},
                {"label": "string"}
            ]
        }

    GET Attribute;
    --------
        [*] results all needs submited
    """

    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._context = {}
        self._uuid = None
        self._user = None
        self._queryset = Need.objects \
            .prefetch_related(Prefetch('user'), Prefetch('items'),
                              Prefetch('location'), Prefetch('offers')) \
            .select_related('user', 'location') \
            .annotate(total_offer=Count('offers'))

    def dispatch(self, request, *args, **kwargs):
        self._uuid = kwargs.get('uuid')
        self._context.update({'request': request})
        self._user = request.user
        return super().dispatch(request, *args, **kwargs)

    def _get_instances(self):
        return self._queryset.filter(user_id=self._user.id) \
            .order_by('-create_at')

    def list(self, request, format='json'):
        instances = self._get_instances()
        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = ListNeedSerializer(paginator, context=self._context,
                                        many=True)
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format='json'):
        instance = self._get_instance()
        serializer = RetrieveNeedSerializer(instance, many=False,
                                            context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic()
    def create(self, request, format='json'):
        serializer = CreateNeedSerializer(data=request.data,
                                          context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            _serializer = RetrieveNeedSerializer(serializer.instance,
                                                 context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @transaction.atomic()
    def partial_update(self, request, uuid=None, format='json'):
        instance = self._get_instance()
        serializer = CreateNeedSerializer(instance, partial=True, many=False,
                                          data=request.data, context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
