import os
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .abstract import AbstractCommonField


class AbstractPropose(AbstractCommonField):
    """
    Listing create Propose
    Everyone with allow Propose role can send Propose
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='proposes')
    listing = models.ForeignKey('procure.Listing', on_delete=models.CASCADE,
                                related_name='proposes', editable=False)
    inquiry = models.ForeignKey('procure.Inquiry', on_delete=models.CASCADE,
                                related_name='proposes')

    class Meta:
        abstract = True
        app_label = 'procure'
        get_latest_by = ['-create_at']
        ordering = ['-create_at']
        verbose_name = _("Propose")
        verbose_name_plural = _("Proposes")

    def __str__(self) -> str:
        return self.inquiry.keyword

    @property
    def count_offers(self):
        return self.offers.count()


class AbstractOffer(AbstractCommonField):
    propose = models.ForeignKey('procure.Propose', on_delete=models.CASCADE,
                                related_name='offers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='offers')

    # if cost filled indicate as whole offer
    cost = models.BigIntegerField(null=True, blank=True)
    discount = models.IntegerField(default=0)
    description = models.TextField(null=True, blank=True)

    can_attend = models.BooleanField(default=False)
    can_attend_radius = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField(default=Decimal(0.0), db_index=True)
    longitude = models.FloatField(default=Decimal(0.0), db_index=True)
    is_newest = models.BooleanField(default=True, editable=False)

    class Meta:
        abstract = True
        app_label = 'procure'
        get_latest_by = ['-create_at']
        ordering = ['-create_at']
        verbose_name = _("Offer")
        verbose_name_plural = _("Offers")

    def __str__(self) -> str:
        return str(self.cost)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        """ Old records is_newest to False """
        old_instances = self.__class__.objects \
            .filter(Q(is_newest=True), Q(propose_id=self.propose.id))

        if self.pk:
            old_instances = old_instances \
                .filter(create_at__lt=self.create_at) \
                .exclude(id=self.pk)

        if old_instances.exists():
            old_instances.update(is_newest=False)

        return super().save(*args, **kwargs)


class AbstractOfferItem(AbstractCommonField):
    """
    Each inquiry item can has standalone offer
    This is because inquiry item may changes cost
    """
    # user maybe has different because each listing has multiple user
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='items')

    offer = models.ForeignKey('procure.Offer', on_delete=models.CASCADE,
                              related_name='items')
    inquiry_item = models.ForeignKey('procure.InquiryItem', on_delete=models.CASCADE,
                                     related_name='items', null=True, blank=True)

    cost = models.BigIntegerField()
    discount = models.IntegerField(default=0)
    quantity = models.IntegerField(default=1)
    description = models.TextField(null=True, blank=True)
    is_available = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'procure'
        ordering = ['create_at']
        verbose_name = _("Offer Item")
        verbose_name_plural = _("Offer Items")

    def __str__(self) -> str:
        return str(self.cost)


class AbstractNegotiation(AbstractCommonField):
    class MediaType(models.TextChoices):
        TEXT = 'text', _("Text")
        ATTACHMENT = 'attachment', _("Attachment")

    propose = models.ForeignKey('procure.Propose', on_delete=models.CASCADE,
                                related_name='negotiations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='negotiations')
    media_type = models.CharField(choices=MediaType.choices, default=MediaType.TEXT,
                                  max_length=15)

    class Meta:
        abstract = True
        app_label = 'procure'
        ordering = ['-create_at']
        verbose_name = _("Negotiation")
        verbose_name_plural = _("Negotiations")

    def __str__(self) -> str:
        return self.get_content_type_display()


class AbstractNegotiationText(AbstractCommonField):
    negotiation = models.OneToOneField('procure.Negotiation', on_delete=models.CASCADE,
                                       related_name='text')
    content = models.TextField()

    class Meta:
        abstract = True
        app_label = 'procure'
        ordering = ['-create_at']
        verbose_name = _("Negotiation Text")
        verbose_name_plural = _("Negotiation Texts")

    def __str__(self) -> str:
        return self.content


class AbstractNegotiationAttachment(AbstractCommonField):
    negotiation = models.ForeignKey('procure.Negotiation', on_delete=models.CASCADE,
                                    related_name='attachments')

    file = models.FileField(upload_to='negotiation/%Y/%m/%d')
    filename = models.CharField(max_length=255, editable=False)
    filepath = models.CharField(max_length=255, editable=False)
    filesize = models.IntegerField(editable=False)
    filemime = models.CharField(max_length=255, editable=False)

    label = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'procure'
        verbose_name = _("Negotiation Attachment")
        verbose_name_plural = _("Negotiation Attachments")

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            base = os.path.basename(self.file.name)
            self.label = base
        super().save(*args, **kwargs)
