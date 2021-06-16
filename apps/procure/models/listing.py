import os
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .abstract import AbstractCommonField


class AbstractListing(AbstractCommonField):
    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    keyword = models.TextField()
    contact = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")

    def __str__(self) -> str:
        return self.label


class AbstractListingState(AbstractCommonField):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Pending")
        APROVED = 'aproved', _("Aproved")
        REJECTED = 'rejected', _("Rejected")

    listing = models.OneToOneField('procure.Listing', on_delete=models.CASCADE,
                                   related_name='state')

    status = models.CharField(choices=Status.choices, default=Status.PENDING,
                              max_length=15)
    is_delete = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing Status")
        verbose_name_plural = _("Listing Status")


class ListingMemberManager(models.QuerySet):
    def _get_defaults(self):
        return self.filter(is_default=True)

    def mark_undefault(self, exclude_uuid=None):
        instances = self._get_defaults().exclude(uuid=exclude_uuid)
        if instances.exists():
            instances.update(is_default=False)


class AbstractListingMember(AbstractCommonField):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='members')
    listing = models.ForeignKey('procure.Listing', on_delete=models.CASCADE,
                                related_name='members')

    is_admin = models.BooleanField(default=False)
    is_creator = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    is_allow_propose = models.BooleanField(default=False)

    objects = ListingMemberManager.as_manager()

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing Member")
        verbose_name_plural = _("Listing Members")

    def __str__(self) -> str:
        return self.label

    @property
    def label(self):
        return '{} {}'.format(self.user.username, self.listing.label)


class AbstractListingOpening(AbstractCommonField):
    class Day(models.IntegerChoices):
        MO = 0, _("Monday")
        TU = 1, _("Tuesday")
        WE = 2, _("Wednesday")
        TH = 3, _("Thursday")
        FR = 4, _("Friday")
        SA = 5, _("Saturday")
        SU = 6, _("Sunday")

    listing = models.ForeignKey('procure.Listing', on_delete=models.CASCADE,
                                related_name='openings')
    day = models.IntegerField(choices=Day.choices)
    open_time = models.TimeField(default='00:00')
    close_time = models.TimeField(default='00:00')
    is_open = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing Opening")
        verbose_name_plural = _("Listing Openings")

    def name(self):
        return self.get_day_display()

    def __str__(self) -> str:
        return self.get_day_display()


class AbstractListingGallery(AbstractCommonField):
    listing = models.ForeignKey('procure.Listing', on_delete=models.CASCADE,
                                related_name='galleries')
    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing Gallery")
        verbose_name_plural = _("Listing Galleries")

    def __str__(self) -> str:
        return self.label


class AbstractListingAttachment(AbstractCommonField):
    listing = models.ForeignKey('procure.Listing', on_delete=models.CASCADE,
                                related_name='attachments')
    gallery = models.ForeignKey('procure.ListingGallery', on_delete=models.CASCADE,
                                related_name='attachments')

    file = models.FileField(upload_to='gallery/%Y/%m/%d')
    filename = models.CharField(max_length=255, editable=False)
    filepath = models.CharField(max_length=255, editable=False)
    filesize = models.IntegerField(editable=False)
    filemime = models.CharField(max_length=255, editable=False)

    label = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing Attachment")
        verbose_name_plural = _("Listing Attachments")

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            base = os.path.basename(self.file.name)
            self.label = base
        super().save(*args, **kwargs)


class AbstractListingLocation(AbstractCommonField):
    listing = models.OneToOneField('procure.Listing', related_name='location',
                                   on_delete=models.CASCADE)
    street_address = models.TextField(
        help_text=_("Jalan Pratu Boestaman No.10"))
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
        verbose_name = _("Listing Location")
        verbose_name_plural = _("Listing Locations")

    def __str__(self) -> str:
        return self.street_address
