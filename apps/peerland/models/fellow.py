from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .abstract import AbstractCommonField


class AbstractBorrower(AbstractCommonField):
    """ 
    An Submission can has multiple Borrowers 
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='borrowers',
                             on_delete=models.CASCADE, null=True, blank=True)
    submission = models.ForeignKey('peerland.Submission', on_delete=models.CASCADE,
                                   related_name='borrowers')

    note = models.TextField(null=True, blank=True)
    is_initiator = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'peerland'
        verbose_name = _("Borrower")
        verbose_name_plural = _("Borrowers")


class AbstractLender(AbstractCommonField):
    """ 
    An Submission can has multiple Lenders 
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='lenders',
                             on_delete=models.CASCADE, null=True, blank=True)
    submission = models.ForeignKey('peerland.Submission', on_delete=models.CASCADE,
                                   related_name='lenders')

    note = models.TextField(null=True, blank=True)
    is_initiator = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'peerland'
        verbose_name = _("Lender")
        verbose_name_plural = _("Lenders")
