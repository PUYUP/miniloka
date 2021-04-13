from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.repair.models.abstract import CommonInfo
from utils.validators import non_python_keyword, identifier_validator


class VarietyChoice(models.TextChoices):
    CAR = 'car', _("Car")
    MOTORCYCLE = 'motorcycle', _("Motorcycle")
    COMPUTER = 'computer', _("Computer")


class AbstractImprove(CommonInfo):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='improves',
                             on_delete=models.SET_NULL, null=True)
    explain = models.TextField()
    variety = models.CharField(choices=VarietyChoice.choices, null=True, max_length=255,
                               validators=[identifier_validator, non_python_keyword])

    class Meta:
        abstract = True
        app_label = 'repair'
        verbose_name = _("Improve")
        verbose_name_plural = _("Improves")

    def __str__(self) -> str:
        return self.explain


class AbstractImproveTask(CommonInfo):
    improve = models.ForeignKey('repair.Improve', related_name='tasks',
                                on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    explain = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=1)

    class Meta:
        abstract = True
        app_label = 'repair'
        verbose_name = _("Improve Task")
        verbose_name_plural = _("Improve Tasks")

    def __str__(self) -> str:
        return self.label


class AbstractImproveLocation(CommonInfo):
    improve = models.OneToOneField('repair.Improve', related_name='location',
                                   on_delete=models.CASCADE)
    street_address = models.TextField(null=True, blank=True)
    street_number = models.CharField(null=True, blank=True, max_length=255)
    route = models.TextField(null=True, blank=True)
    intersection = models.CharField(null=True, blank=True, max_length=255)
    political = models.CharField(null=True, blank=True, max_length=255)
    country = models.CharField(null=True, blank=True, max_length=255, db_index=True)
    administrative_area_level_1 = models.CharField(null=True, blank=True, max_length=255, db_index=True)
    administrative_area_level_2 = models.CharField(null=True, blank=True, max_length=255, db_index=True)
    administrative_area_level_3 = models.CharField(null=True, blank=True, max_length=255)
    administrative_area_level_4 = models.CharField(null=True, blank=True, max_length=255)
    administrative_area_level_5 = models.CharField(null=True, blank=True, max_length=255)
    colloquial_area = models.CharField(null=True, blank=True, max_length=255)
    locality = models.CharField(null=True, blank=True, max_length=255)
    sublocality = models.CharField(null=True, blank=True, max_length=255)
    sublocality_level_1 = models.CharField(null=True, blank=True, max_length=255)
    sublocality_level_2 = models.CharField(null=True, blank=True, max_length=255)
    neighborhood = models.CharField(null=True, blank=True, max_length=255)
    premise = models.CharField(null=True, blank=True, max_length=255)
    subpremise = models.CharField(null=True, blank=True, max_length=255)
    plus_code = models.CharField(null=True, blank=True, max_length=255, db_index=True)
    postal_code = models.CharField(null=True, blank=True, max_length=255, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0), db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0), db_index=True)

    class Meta:
        abstract = True
        app_label = 'repair'
        verbose_name = _("Improve Location")
        verbose_name_plural = _("Improve Location")

    def __str__(self) -> str:
        return self.street_address
