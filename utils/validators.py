import uuid
import keyword

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.http.response import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.decorators import decorator_from_middleware
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags, escape
from django.utils.regex_helper import _lazy_re_compile
from rest_framework import serializers


identifier_validator = RegexValidator(
    regex=_lazy_re_compile(r'^[a-zA-Z_][a-zA-Z_]*$'),
    message=_("Can only contain the letters a-z and underscores.")
)


validate_msisdn = RegexValidator(
    regex=_lazy_re_compile(r'\+?([ -]?\d+)+|\(\d+\)([ -]\d+)'),
    message=_("MSISDN format invalid.")
)


def validate_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> validate_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> validate_uuid('c9bf9e58')
    False
    """
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def non_python_keyword(value):
    if keyword.iskeyword(value):
        raise ValidationError(
            _("This field is invalid as its value is forbidden.")
        )
    return value


def make_safe_string(data):
    # clear unsafe html string
    for key in data:
        string = data.get(key, None)
        if string and isinstance(string, str):
            string = escape(strip_tags(string))
            data[key] = string
    return data


class CleanValidateMixin(serializers.ModelSerializer):
    def validate(self, attrs):
        # exclude all field with type list or dict
        attr = {
            x: attrs.get(x) for x in list(attrs) 
            if not isinstance(attrs.get(x), list) and not isinstance(attrs.get(x), dict)
        }

        # add current instance value
        if not self.instance:
            instance = self.Meta.model(**attr)
            if hasattr(instance, 'clean'):
                instance.clean(**self.context)
        else:
            if isinstance(self.instance, QuerySet):
                uuid = attrs.get('uuid')
                instance = next((x for x in self.instance if x.uuid == uuid), None)
                
                if instance is not None:
                    for x in attr:
                        setattr(instance, x, attr.get(x))
                    instance.clean(**self.context)
            else:
                for x in attr:
                    setattr(self.instance, x, attr.get(x))
                self.instance.clean(**self.context)

        return attrs


class CsrfViewMiddlewareAPI(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return JsonResponse({'detail': reason}, status=406)


csrf_protect_drf = decorator_from_middleware(CsrfViewMiddlewareAPI)
csrf_protect_drf.__name__ = "csrf_protect_drf"
csrf_protect_drf.__doc__ = """
This decorator adds CSRF protection in exactly the same way as
CsrfViewMiddleware, but it can be used on a per view basis.  Using both, or
using the decorator multiple times, is harmless and efficient.
"""
