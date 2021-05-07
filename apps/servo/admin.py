from django.contrib import admin
from django.contrib.auth import get_user_model
from utils.generals import get_model

Need = get_model('servo', 'Need')
NeedItem = get_model('servo', 'NeedItem')
NeedLocation = get_model('servo', 'NeedLocation')

NeedTag = get_model('servo', 'Tag')
NeedTagItem = get_model('servo', 'TagItem')
TaggitTag = get_model('taggit', 'Tag')

Listing = get_model('servo', 'Listing')
ListingMember = get_model('servo', 'ListingMember')
ListingOpening = get_model('servo', 'ListingOpening')
ListingGallery = get_model('servo', 'ListingGallery')
ListingAttachment = get_model('servo', 'ListingAttachment')
ListingLocation = get_model('servo', 'ListingLocation')

Offer = get_model('servo', 'Offer')
OfferRate = get_model('servo', 'OfferRate')
OfferItem = get_model('servo', 'OfferItem')
OfferItemRate = get_model('servo', 'OfferItemRate')
OfferDiscussion = get_model('servo', 'OfferDiscussion')
OfferDiscussionText = get_model('servo', 'OfferDiscussionText')
OfferDiscussionAttachment = get_model('servo', 'OfferDiscussionAttachment')


# NEED
class NeedItemInline(admin.StackedInline):
    model = NeedItem


class NeedLocationInline(admin.StackedInline):
    model = NeedLocation


class NeedExtend(admin.ModelAdmin):
    model = Need
    inlines = [NeedItemInline, NeedLocationInline, ]
    readonly_fields = ['tags', ]

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('user', 'location') \
            .select_related('user', 'location')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('profile') \
                .select_related('profile')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Need, NeedExtend)

admin.site.unregister(TaggitTag)
admin.site.register(NeedTag)
admin.site.register(NeedTagItem)


# LISTING
class ListingOpeningInline(admin.StackedInline):
    model = ListingOpening


class ListingLocationInline(admin.StackedInline):
    model = ListingLocation


class ListingMemberInline(admin.StackedInline):
    model = ListingMember


class ListingExtend(admin.ModelAdmin):
    model = Listing
    inlines = [ListingOpeningInline, ListingMemberInline,
               ListingLocationInline, ]


admin.site.register(Listing, ListingExtend)
admin.site.register(ListingMember)
admin.site.register(ListingGallery)
admin.site.register(ListingAttachment)


# OFFER
class OfferRateInline(admin.StackedInline):
    model = OfferRate


class OfferItemRateInline(admin.StackedInline):
    model = OfferItemRate


class OfferExtend(admin.ModelAdmin):
    model = Offer
    inlines = [OfferRateInline, ]


class OfferItemExtend(admin.ModelAdmin):
    model = OfferItem
    inlines = [OfferItemRateInline, ]


admin.site.register(Offer, OfferExtend)
admin.site.register(OfferItem, OfferItemExtend)


# DISCUSSION
class OfferDiscussionTextInline(admin.StackedInline):
    model = OfferDiscussionText


class OfferDiscussionAttachmentInline(admin.StackedInline):
    model = OfferDiscussionAttachment


class OfferDiscussionExtend(admin.ModelAdmin):
    model = OfferDiscussion
    inlines = [OfferDiscussionTextInline, OfferDiscussionAttachmentInline, ]


admin.site.register(OfferDiscussion, OfferDiscussionExtend)
