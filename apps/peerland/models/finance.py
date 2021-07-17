from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .abstract import AbstractCommonField


class AbstractPayment(AbstractCommonField):
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

    submission = models.ForeignKey('peerland.Submission', related_name='payments',
                                   on_delete=models.CASCADE)
    # payed by
    borrower = models.ForeignKey('peerland.Borrower', related_name='payments',
                                 on_delete=models.CASCADE)

    # who received money
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='payments',
                                  on_delete=models.SET_NULL, null=True, blank=True)

    due_at = models.DateTimeField()
    paid_at = models.DateTimeField()
    tenor_to = models.IntegerField()
    amount = models.BigIntegerField()
    channel = models.CharField(choices=Channel.choices, default=Channel.CASH,
                               max_length=15)
    note = models.TextField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'peerland'
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self) -> str:
        return self.submission.borrower.name
