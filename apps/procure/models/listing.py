import os
from decimal import Decimal

from django.db import models, transaction
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from utils.validators import non_python_keyword, identifier_validator
from .abstract import AbstractCommonField


class AbstractListing(AbstractCommonField):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Pending")
        APPROVED = 'approved', _("Approved")
        REJECTED = 'rejected', _("Rejected")

    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    keyword = models.TextField()
    contact = models.JSONField(null=True, blank=True)
    status = models.CharField(choices=Status.choices,
                              default=Status.PENDING, max_length=15)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")

    def __str__(self) -> str:
        return self.label

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)

        # save original values, when model is loaded from database,
        # in a separate attribute on the model
        instance._loaded_values = dict(zip(field_names, values))

        return instance

    def save(self, *args, **kwargs):
        if not self._state.adding:
            # check if status is being updated
            if self._loaded_values['status'] != self.status and self.pk:
                self.update_listing_state()
        return super().save(*args, **kwargs)

    @transaction.atomic()
    def update_listing_state(self):
        self.states.model.objects \
            .create(listing_id=self.pk, status=self.status)


class AbstractListingState(AbstractCommonField):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Pending")
        APPROVED = 'approved', _("Approved")
        REJECTED = 'rejected', _("Rejected")

    listing = models.ForeignKey('procure.Listing', on_delete=models.CASCADE,
                                related_name='states')
    status = models.CharField(choices=Status.choices,
                              default=Status.PENDING, max_length=15)
    note = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing State")
        verbose_name_plural = _("Listing States")

    def __str__(self) -> str:
        return self.get_status_display()


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
    is_allow_offer = models.BooleanField(default=False)

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
    identifier = models.CharField(max_length=25, null=True, blank=True,
                                  validators=[non_python_keyword, identifier_validator])

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


class AbstractListingProduct(AbstractCommonField):
    listing = models.ForeignKey('procure.Listing', on_delete=models.CASCADE,
                                related_name='products')

    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing Product")
        verbose_name_plural = _("Listing Products")

    def __str__(self) -> str:
        return self.label


class AbstractListingProductAttachment(AbstractCommonField):
    listing = models.ForeignKey('procure.ListingProduct', on_delete=models.CASCADE,
                                related_name='attachments')

    file = models.FileField(upload_to='product/%Y/%m/%d')
    filename = models.CharField(max_length=255, editable=False)
    filepath = models.CharField(max_length=255, editable=False)
    filesize = models.IntegerField(editable=False)
    filemime = models.CharField(max_length=255, editable=False)

    label = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Listing Product Attachment")
        verbose_name_plural = _("Listing Product Attachments")

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
    street_address = models.TextField(help_text=_("Jalan Giri Manuk"))
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
