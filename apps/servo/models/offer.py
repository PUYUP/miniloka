import os
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .abstract import AbstractCommonField


class AbstractOffer(AbstractCommonField):
    """
    Listing create offer
    Everyone with allow offer role can send Offer
    """
    listing = models.ForeignKey('servo.Listing', on_delete=models.CASCADE,
                                related_name='offers', editable=False)
    need = models.ForeignKey('servo.Need', on_delete=models.CASCADE,
                             related_name='offers')

    class Meta:
        abstract = True
        app_label = 'servo'
        get_latest_by = ['-create_at']
        ordering = ['-create_at']
        verbose_name = _("Offer")
        verbose_name_plural = _("Offers")

    def __str__(self) -> str:
        return self.need.description

    @property
    def count_rates(self):
        return self.rates.count()


class AbstractOfferRate(AbstractCommonField):
    """
    Fill offer cost
    -------------
    1st offer 10.000
    2st offer 9.500
    ...n
    """
    offer = models.ForeignKey('servo.Offer', on_delete=models.CASCADE,
                              related_name='rates')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='rates')
    cost = models.BigIntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    can_goto = models.BooleanField(default=True)
    can_goto_radius = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=19, decimal_places=16,
                                   default=Decimal(0.0), db_index=True)
    longitude = models.DecimalField(max_digits=19, decimal_places=16,
                                    default=Decimal(0.0), db_index=True)
    is_newest = models.BooleanField(default=True, editable=False)

    class Meta:
        abstract = True
        app_label = 'servo'
        get_latest_by = ['-create_at']
        ordering = ['-create_at']
        verbose_name = _("Offer Rate")
        verbose_name_plural = _("Offer Rates")

    def __str__(self) -> str:
        return str(self.cost)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        """ Old records is_newest to False """
        old_instances = self.__class__.objects \
            .filter(Q(is_newest=True), Q(offer_id=self.offer.id))

        if self.pk:
            old_instances = old_instances \
                .filter(create_at__lt=self.create_at) \
                .exclude(id=self.pk)

        if old_instances.exists():
            old_instances.update(is_newest=False)

        return super().save(*args, **kwargs)


class AbstractOfferItem(AbstractCommonField):
    """
    Each need item can has standalone offer
    """
    offer = models.ForeignKey('servo.Offer', on_delete=models.CASCADE,
                              related_name='items')
    needitem = models.ForeignKey('servo.NeedItem', on_delete=models.CASCADE,
                                 related_name='items', null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'servo'
        ordering = ['-create_at']
        verbose_name = _("Offer Item")
        verbose_name_plural = _("Offer Items")

    def __str__(self) -> str:
        return self.needitem.label


class AbstractOfferItemRate(AbstractCommonField):
    """
    1st offer 5.000
    2st offer 3.500
    ...n
    """
    offer_item = models.ForeignKey('servo.OfferItem', on_delete=models.CASCADE,
                                   related_name='item_rates')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='item_rates')

    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    cost = models.BigIntegerField()
    discount = models.IntegerField(default=0)
    is_newest = models.BooleanField(default=True, editable=False)

    class Meta:
        abstract = True
        app_label = 'servo'
        ordering = ['-create_at']
        verbose_name = _("Offer Item Rate")
        verbose_name_plural = _("Offer Item Rates")

    def __str__(self) -> str:
        return str(self.cost)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        old_instances = self.__class__.objects \
            .filter(
                Q(is_newest=True) | Q(create_at__lt=self.create_at),
                Q(offer_item_id=self.offer_item.id)
            ) \
            .exclude(id=self.pk)

        if old_instances.exists():
            old_instances.update(is_newest=False)

        return super().save(*args, **kwargs)


class AbstractOfferDiscussion(AbstractCommonField):
    class Variety(models.TextChoices):
        TEXT = 'text', _("Text")
        ATTACHMENT = 'attachment', _("Attachment")

    offer = models.ForeignKey('servo.Offer', on_delete=models.CASCADE,
                              related_name='discussions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='discussions')
    variety = models.CharField(choices=Variety.choices, default=Variety.TEXT,
                               max_length=15)

    class Meta:
        abstract = True
        app_label = 'servo'
        ordering = ['-create_at']
        verbose_name = _("Offer Discussion")
        verbose_name_plural = _("Offer Discussions")

    def __str__(self) -> str:
        return self.get_variety_display()


class AbstractOfferDiscussionText(AbstractCommonField):
    offerdiscussion = models.OneToOneField('servo.OfferDiscussion', on_delete=models.CASCADE,
                                           related_name='text')
    content = models.TextField()

    class Meta:
        abstract = True
        app_label = 'servo'
        ordering = ['-create_at']
        verbose_name = _("Offer Discussion Text")
        verbose_name_plural = _("Offer Discussion Texts")

    def __str__(self) -> str:
        return self.content


class AbstractOfferDiscussionAttachment(AbstractCommonField):
    offerdiscussion = models.ForeignKey('servo.OfferDiscussion', on_delete=models.CASCADE,
                                        related_name='attachments')

    file = models.FileField(upload_to='discussion/%Y/%m/%d')
    filename = models.CharField(max_length=255, editable=False)
    filepath = models.CharField(max_length=255, editable=False)
    filesize = models.IntegerField(editable=False)
    filemime = models.CharField(max_length=255, editable=False)

    label = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'servo'
        verbose_name = _("Offer Discussion Attachment")
        verbose_name_plural = _("Offer Discussion Attachments")

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            base = os.path.basename(self.file.name)
            self.label = base
        super().save(*args, **kwargs)
