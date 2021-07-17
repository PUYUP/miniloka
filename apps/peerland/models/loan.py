import os
from decimal import Decimal

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey  # noqa

from utils.validators import non_python_keyword, identifier_validator
from .abstract import AbstractCommonField


class AbstractSubmission(AbstractCommonField):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Pending")
        APPROVED = 'approved', _("Approved")
        REJECTED = 'rejected', _("Rejected")

    class Period(models.TextChoices):
        MONTHLY = 'monthly', _("Monthly")
        BIWEEKLY = 'biweekly', _("Biweekly")

    # ex: an Order from procure
    burden_content_type = models.ForeignKey(
        ContentType,
        related_name='submission_burden',
        on_delete=models.CASCADE
    )
    burden_object_id = models.CharField(max_length=255)
    burden = GenericForeignKey('burden_content_type', 'burden_object_id')

    description = models.TextField(null=True, blank=True)
    amount = models.BigIntegerField()
    tenor = models.IntegerField()
    period = models.CharField(max_length=15, choices=Period.choices,
                              default=Period.MONTHLY)
    start_at = models.DateTimeField()
    due_at = models.DateTimeField()
    repayment_at = models.DateTimeField()
    status = models.CharField(choices=Status.choices,
                              default=Status.PENDING, max_length=15)

    class Meta:
        abstract = True
        app_label = 'peerland'
        verbose_name = _("Submission")
        verbose_name_plural = _("Submissions")

    def __str__(self) -> str:
        return self.order or str(self.amount)

    def save(self, *args, **kwargs):
        if self.listing:
            self.listing = self.order.propose.listing

        if not self._state.adding and hasattr(self, '_loaded_values'):
            # check if status is being updated
            if self._loaded_values['status'] != self.status and self.pk:
                self.update_submission_state()
        return super().save(*args, **kwargs)

    @transaction.atomic()
    def update_submission_state(self):
        self.states.model.objects \
            .create(listing_id=self.pk, status=self.status)


class AbstractTerm(AbstractCommonField):
    class MetaKey(models.TextChoices):
        TERM_IDCARD_NUMBER = 'term_idcard_number', _("Term IDCard Number")
        TERM_MOTHER_NAME = 'term_mother_name', _("Term Mother Name")

    submission = models.ForeignKey('peerland.Submission', on_delete=models.CASCADE,
                                   related_name='terms')
    meta_key = models.CharField(max_length=255, choices=MetaKey.choices)
    meta_value = models.TextField()

    class Meta:
        abstract = True
        app_label = 'peerland'
        verbose_name = _("Meta Data")
        verbose_name_plural = _("Meta Datas")

    def __str__(self) -> str:
        return self.get_meta_key_display()


class AbstractState(AbstractCommonField):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Pending")
        APPROVED = 'approved', _("Approved")
        REJECTED = 'rejected', _("Rejected")

    submission = models.ForeignKey('peerland.Submission', on_delete=models.CASCADE,
                                   related_name='states')
    status = models.CharField(choices=Status.choices,
                              default=Status.PENDING, max_length=15)
    note = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'peerland'
        verbose_name = _("State")
        verbose_name_plural = _("States")

    def __str__(self) -> str:
        return self.get_status_display()


class AbstractAttachment(AbstractCommonField):
    class Identifier(models.TextChoices):
        VIDEO_IDCARD = 'photo_idcard', _("ID Card")
        VIDEO_SELFIE = 'video_selfie', _("Video Selfie + ID Card")
        VIDEO_WITH_PARTNER = 'photo_with_partner', _("Photo With Partner")
        VIDEO_WITH_PRODUCT = 'photo_with_product', _("Photo With Product")

    submission = models.ForeignKey('peerland.Submission', on_delete=models.CASCADE,
                                   related_name='attachments')

    file = models.FileField(upload_to='submission/%Y/%m/%d')
    filename = models.CharField(max_length=255, editable=False)
    filepath = models.CharField(max_length=255, editable=False)
    filesize = models.IntegerField(editable=False)
    filemime = models.CharField(max_length=255, editable=False)

    label = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)
    identifier = models.CharField(max_length=25, null=True, blank=True,
                                  validators=[non_python_keyword,
                                              identifier_validator],
                                  choices=Identifier.choices,
                                  default=Identifier.VIDEO_IDCARD)

    class Meta:
        abstract = True
        app_label = 'peerland'
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            base = os.path.basename(self.file.name)
            self.label = base
        super().save(*args, **kwargs)


class AbstractLocation(AbstractCommonField):
    submission = models.OneToOneField('peerland.Submission', related_name='location',
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
        app_label = 'peerland'
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    def __str__(self) -> str:
        return self.street_address
