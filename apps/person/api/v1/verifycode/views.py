from django.db import transaction
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from utils.validators import csrf_protect_drf
from utils.generals import get_model
from .serializers import (
    CreateVerifyCodeSerializer,
    RetrieveVerifyCodeSerialzer,
    ValidateVerifyCodeSerializer
)

VerifyCode = get_model('person', 'VerifyCode')


class VerifyCodeApiView(viewsets.ViewSet):
    """
    POST
    ---------------

    Param:

        {
            "email": "my@email.com",
            "msisdn": "09284255",
            "challenge": "EMAIL_VALIDATION"
        }

    PATCH
    --------------

    Param:

         {
            "email": "my@email.com",
            "msisdn": "09284255",
            "challenge": "EMAIL_VALIDATION",
            "token": "string"
        }

    Rules:

        username only used if user don't have active email
        eg; email auto-generate by system

        If email provided, msisdn not required
        If msisdn provide, email not required
    """
    lookup_field = 'passcode'
    lookup_value_regex = '[^/]+'
    permission_classes = (AllowAny,)

    def __init__(self, **kwargs):
        self._queryset = self._get_queryset()
        self._context = {}
        self._passcode = None
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self._passcode = kwargs.get('passcode')
        self._context.update({'request': request})
        return super().dispatch(request, *args, **kwargs)

    def _get_queryset(self):
        """General query affected for entire object"""
        query = VerifyCode.objects
        return query

    def _get_object(self):
        """Return single object"""
        try:
            object = self._queryset.get(passcode=self._passcode)
        except ObjectDoesNotExist:
            raise NotFound()
        return object

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        serializer = CreateVerifyCodeSerializer(data=request.data,
                                                context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            _serializer = RetrieveVerifyCodeSerialzer(
                serializer.instance, context=self._context, many=False)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, passcode=None):
        # Instance set to objects None
        self._context.update({'passcode': passcode})
        serializer = ValidateVerifyCodeSerializer(VerifyCode.objects.none(), data=request.data, partial=False,
                                                  context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            _serializer = RetrieveVerifyCodeSerialzer(
                serializer.instance, context=self._context, many=False)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
