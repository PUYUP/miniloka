import os
from decimal import Decimal

from django.db import models, transaction
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from utils.validators import non_python_keyword, identifier_validator
from .abstract import AbstractCommonField


class AbstractInstallment(AbstractCommonField):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Pending")
        APPROVED = 'approved', _("Approved")
        REJECTED = 'rejected', _("Rejected")

    lender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='installment_lenders',
                               on_delete=models.CASCADE, null=True, blank=True)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='installment_borrowers',
                                 on_delete=models.CASCADE)
    order = models.OneToOneField('procure.Order', related_name='installment',
                                 on_delete=models.CASCADE)
    listing = models.ForeignKey('procure.Listing', related_name='installments',
                                on_delete=models.CASCADE, editable=False)

    amount = models.BigIntegerField()
    tenor = models.IntegerField()
    start_at = models.DateTimeField()
    due_at = models.DateTimeField()
    status = models.CharField(choices=Status.choices,
                              default=Status.PENDING, max_length=15)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Installment")
        verbose_name_plural = _("Installments")

    def __str__(self) -> str:
        return self.user.name

    def save(self, *args, **kwargs):
        self.listing = self.order.propose.listing

        if not self._state.adding:
            # check if status is being updated
            if self._loaded_values['status'] != self.status and self.pk:
                self.update_installment_state()
        return super().save(*args, **kwargs)

    @transaction.atomic()
    def update_installment_state(self):
        self.states.model.objects \
            .create(listing_id=self.pk, status=self.status)


class AbstractInstallmentState(AbstractCommonField):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Pending")
        APPROVED = 'approved', _("Approved")
        REJECTED = 'rejected', _("Rejected")

    installment = models.ForeignKey('procure.Installment', on_delete=models.CASCADE,
                                    related_name='states')
    status = models.CharField(choices=Status.choices,
                              default=Status.PENDING, max_length=15)
    note = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Installment State")
        verbose_name_plural = _("Installment States")

    def __str__(self) -> str:
        return self.get_status_display()


class AbstractInstallmentAttachment(AbstractCommonField):
    installment = models.ForeignKey('procure.Installment', on_delete=models.CASCADE,
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
        verbose_name = _("Installment Attachment")
        verbose_name_plural = _("Installment Attachments")

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            base = os.path.basename(self.file.name)
            self.label = base
        super().save(*args, **kwargs)


class AbstractInstallmentPayment(AbstractCommonField):
    class Channel(models.TextChoices):
        CASH = 'cash', _("Cash")
        CREDIT_CARD = 'credit_card', _("Credit Card")
        BCA_VA = 'bca_va', _("BCA Virtual Account")
        PERMATA_VA = 'permata_va', _("Permata Virtual Account")
        BNI_VA = 'bni_va', _("BNI Virtual Account")
        BRI_VA = 'bri_va', _("BRI Virtual Account")
        ECHANNEL = 'echannel', _("Mandiri Bill")
        GOPAY = 'gopay', _("GoPay")
        BCA_KLIKBCA = 'bca_klikbca', _("KlikBCA")
        BCA_KLIKPAY = 'bca_klikpay', _("BCA KlikPay")
        CIMB_CLICKS = 'cimb_clicks', _("CIMB Clicks")
        DANAMON_ONLINE = 'danamon_online', _("Danamon Online Banking")
        BRI_EPAY = 'bri_epay', _("BRI Epay")
        INDOMARET = 'indomaret', _("Indomaret")
        ALFAMART = 'alfamart', _("Alfamart")
        AKULAKU = 'akulaku', _("Akulaku")
        SHOPEEPAY = 'shopeepay', _("ShopeePay")

    installment = models.ForeignKey('procure.Installment', related_name='payments',
                                    on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='payments',
                                  on_delete=models.SET_NULL, null=True, blank=True)

    due_at = models.DateTimeField()
    paid_at = models.DateTimeField()
    amount = models.BigIntegerField()
    channel = models.CharField(choices=Channel.choices, default=Channel.CASH,
                               max_length=15)
    note = models.TextField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Installment Payment")
        verbose_name_plural = _("Installment Payments")

    def __str__(self) -> str:
        return self.installment.borrower.name


class AbstractInstallmentLocation(AbstractCommonField):
    listing = models.OneToOneField('procure.Installment', related_name='location',
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
        verbose_name = _("Installment Location")
        verbose_name_plural = _("Installment Locations")

    def __str__(self) -> str:
        return self.street_address
