from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .abstract import AbstractCommonField


class AbstractOrder(AbstractCommonField):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='orders')
    inquiry = models.ForeignKey('procure.Inquiry', on_delete=models.CASCADE,
                                related_name='orders')
    propose = models.ForeignKey('procure.Propose', on_delete=models.CASCADE,
                                related_name='orders', editable=False)
    offer = models.OneToOneField('procure.Offer', on_delete=models.CASCADE,
                                 related_name='order')

    cost = models.BigIntegerField(default=0, blank=True)
    discount = models.IntegerField(default=0)
    description = models.TextField(null=True, blank=True)
    secret = models.CharField(max_length=15, editable=False)

    latitude = models.FloatField(default=Decimal(0.0), db_index=True)
    longitude = models.FloatField(default=Decimal(0.0), db_index=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        get_latest_by = ['create_at']
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self) -> str:
        return self.user.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.propose = self.offer.propose
            self.cost = self.offer.cost
            self.discount = self.offer.discount
            self.description = self.offer.description
            self.latitude = self.offer.latitude
            self.longitude = self.offer.longitude

        return super().save(*args, **kwargs)


class AbstractOrderItem(AbstractCommonField):
    order = models.ForeignKey('procure.Order', on_delete=models.CASCADE,
                              related_name='items')
    offer_item = models.ForeignKey('procure.OfferItem', on_delete=models.CASCADE,
                                   related_name='items')

    label = models.CharField(max_length=255, null=True, blank=True)
    cost = models.BigIntegerField(default=0)
    discount = models.IntegerField(default=0)
    quantity = models.IntegerField(default=1)
    description = models.TextField(null=True, blank=True)

    is_available = models.BooleanField(default=False)
    is_additional = models.BooleanField(default=False, null=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        get_latest_by = ['create_at']
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def __str__(self) -> str:
        return self.label
