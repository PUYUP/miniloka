import os
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from taggit.managers import TaggableManager

from apps.procure.models.abstract import AbstractCommonField
from .tag import TagItem


class AbstractInquiry(AbstractCommonField):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='inquiries',
                             on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    keyword = models.TextField()
    tags = TaggableManager(through=TagItem, blank=True)
    open_at = models.DateTimeField(null=True, blank=True)
    close_at = models.DateTimeField(blank=True, null=True)
    is_open = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        get_latest_by = ['create_at']
        verbose_name = _("Inquiry")
        verbose_name_plural = _("Inquiries")

    def __str__(self) -> str:
        return self.keyword

    def save(self, *args, **kwargs):
        if not self.pk:
            open_at = self.open_at or timezone.now()
            self.close_at = timezone.make_aware(
                open_at.date()) + timezone.timedelta(days=7)
        super().save(*args, **kwargs)


class AbstractInquiryItem(AbstractCommonField):
    inquiry = models.ForeignKey('procure.Inquiry', related_name='items',
                                on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    order = models.IntegerField(default=1)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Inquiry Item")
        verbose_name_plural = _("Inquiry Items")

    def __str__(self) -> str:
        return self.label


class AbstractInquiryItemAttachment(AbstractCommonField):
    inquiry_item = models.ForeignKey('procure.InquiryItem', on_delete=models.CASCADE,
                                     related_name='attachments')

    file = models.FileField(upload_to='inquiry/%Y/%m/%d')
    filename = models.CharField(max_length=255, editable=False)
    filepath = models.CharField(max_length=255, editable=False)
    filesize = models.IntegerField(editable=False)
    filemime = models.CharField(max_length=255, editable=False)

    label = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Inquiry Item Attachment")
        verbose_name_plural = _("Inquiry Item Attachments")

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            base = os.path.basename(self.file.name)
            self.label = base
        super().save(*args, **kwargs)


class AbstractInquiryLocation(AbstractCommonField):
    inquiry = models.OneToOneField('procure.Inquiry', related_name='location',
                                   on_delete=models.CASCADE)
    street_address = models.TextField(help_text=_("Jalan Pratu Boestaman No.10"),
                                      null=True, blank=True)
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
    latitude = models.FloatField(default=Decimal(0.0), db_index=True)
    longitude = models.FloatField(default=Decimal(0.0), db_index=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Inquiry Location")
        verbose_name_plural = _("Inquiry Locations")

    def __str__(self) -> str:
        return '{}, {}'.format(self.latitude, self.longitude)
