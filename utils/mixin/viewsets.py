from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError as ValidationErrorResponse
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class ViewSetGetObjMixin(ViewSet):
    @transaction.atomic
    def get_object(self, uuid=None, is_update=False):
        queryset = self.queryset()

        try:
            if is_update:
                queryset = queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = queryset.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValidationError as e:
            raise ValidationErrorResponse(detail=str(e))

        return queryset


class ViewSetDestroyObjMixin(ViewSet):
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)
        
        try:
            queryset.delete(request=request)
        except ValidationError as e:
            raise NotAcceptable(detail=' '.join(e))

        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_200_OK)
