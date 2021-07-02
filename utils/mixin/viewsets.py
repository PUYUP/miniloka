from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class ViewSetGetObjMixin(ViewSet):
    def _get_instance(self, is_update=False):
        try:
            if is_update:
                return self._get_instances().select_for_update() \
                    .get(uuid=self._uuid)
            else:
                return self._get_instances().get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Not found"))
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))


class ViewSetDestroyObjMixin(ViewSet):
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        instance = self._get_instance()

        try:
            instance.delete()
        except DjangoValidationError as e:
            raise NotAcceptable(detail=' '.join(e))
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_200_OK)
