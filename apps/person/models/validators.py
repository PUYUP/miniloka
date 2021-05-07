from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class MsisdnValidator(validators.RegexValidator):
    regex = r'^[1-9][0-9]{10,14}+\Z'
    message = _(
        'Enter a valid msisdn. This value may contain only numbers.'
    )
    flags = 0
