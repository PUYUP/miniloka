import os
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from taggit.managers import TaggableManager

from apps.servo.models.abstract import AbstractCommonField
from utils.validators import non_python_keyword, identifier_validator
from .tag import TagItem


class AbstractNeed(AbstractCommonField):
    class Variety(models.TextChoices):
        REPAIR = 'repair', _("Perbaikan")
        BUYING = 'buying', _("Pembelian")
        LOOKING = 'looking', _("Pencarian")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='needs',
                             on_delete=models.CASCADE)
    variety = models.CharField(choices=Variety.choices, max_length=255,
                               validators=[identifier_validator, non_python_keyword])
    description = models.TextField()
    tags = TaggableManager(through=TagItem, blank=True)

    class Meta:
        abstract = True
        app_label = 'servo'
        get_latest_by = ['create_at']
        verbose_name = _("Need")
        verbose_name_plural = _("Needs")

    def __str__(self) -> str:
        return self.description

    @property
    def variety_label(self):
        return self.get_variety_display()


class AbstractNeedItem(AbstractCommonField):
    need = models.ForeignKey('servo.Need', related_name='items',
                             on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=1)

    class Meta:
        abstract = True
        app_label = 'servo'
        verbose_name = _("Need Item")
        verbose_name_plural = _("Need Items")

    def __str__(self) -> str:
        return self.label


class AbstractNeedItemAttachment(AbstractCommonField):
    needitem = models.ForeignKey('servo.NeedItem', on_delete=models.CASCADE,
                                 related_name='attachments')

    file = models.FileField(upload_to='need/%Y/%m/%d')
    filename = models.CharField(max_length=255, editable=False)
    filepath = models.CharField(max_length=255, editable=False)
    filesize = models.IntegerField(editable=False)
    filemime = models.CharField(max_length=255, editable=False)

    label = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'servo'
        verbose_name = _("Need Item Attachment")
        verbose_name_plural = _("Need Item Attachments")

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            base = os.path.basename(self.file.name)
            self.label = base
        super().save(*args, **kwargs)


class AbstractNeedLocation(AbstractCommonField):
    need = models.OneToOneField('servo.Need', related_name='location',
                                on_delete=models.CASCADE)
    street_address = models.TextField(null=True, blank=True)
    street_number = models.CharField(null=True, blank=True, max_length=255)
    route = models.TextField(null=True, blank=True)
    intersection = models.CharField(null=True, blank=True, max_length=255)
    political = models.CharField(null=True, blank=True, max_length=255)
    country = models.CharField(null=True, blank=True, max_length=255,
                               db_index=True)
    administrative_area_level_1 = models.CharField(null=True, blank=True,
                                                   max_length=255, db_index=True)
    administrative_area_level_2 = models.CharField(null=True, blank=True,
                                                   max_length=255, db_index=True)
    administrative_area_level_3 = models.CharField(null=True, blank=True,
                                                   max_length=255)
    administrative_area_level_4 = models.CharField(null=True, blank=True,
                                                   max_length=255)
    administrative_area_level_5 = models.CharField(null=True, blank=True,
                                                   max_length=255)
    colloquial_area = models.CharField(null=True, blank=True, max_length=255)
    locality = models.CharField(null=True, blank=True, max_length=255)
    sublocality = models.CharField(null=True, blank=True, max_length=255)
    sublocality_level_1 = models.CharField(null=True, blank=True,
                                           max_length=255)
    sublocality_level_2 = models.CharField(null=True, blank=True,
                                           max_length=255)
    neighborhood = models.CharField(null=True, blank=True, max_length=255)
    premise = models.CharField(null=True, blank=True, max_length=255)
    subpremise = models.CharField(null=True, blank=True, max_length=255)
    plus_code = models.CharField(null=True, blank=True, max_length=255,
                                 db_index=True)
    postal_code = models.CharField(null=True, blank=True, max_length=255,
                                   db_index=True)
    latitude = models.DecimalField(max_digits=19, decimal_places=16,
                                   default=Decimal(0.0), db_index=True)
    longitude = models.DecimalField(max_digits=19, decimal_places=16,
                                    default=Decimal(0.0), db_index=True)

    class Meta:
        abstract = True
        app_label = 'servo'
        verbose_name = _("Need Location")
        verbose_name_plural = _("Need Locations")

    def __str__(self) -> str:
        return self.street_address or self.need.description
