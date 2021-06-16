from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.models import GenericTaggedItemBase, TagBase


class Tag(TagBase):
    description = models.TextField(null=True, blank=True)

    class Meta:
        app_label = 'procure'
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class TagItem(GenericTaggedItemBase):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s"
    )

    class Meta:
        app_label = 'procure'
        verbose_name = _("Tag Item")
        verbose_name_plural = _("Tag Items")
