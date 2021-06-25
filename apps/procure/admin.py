from django.contrib import admin
from django.contrib.auth import get_user_model
from utils.generals import get_model

Inquiry = get_model('procure', 'Inquiry')
InquiryItem = get_model('procure', 'InquiryItem')
InquiryLocation = get_model('procure', 'InquiryLocation')

InquiryTag = get_model('procure', 'Tag')
InquiryTagItem = get_model('procure', 'TagItem')
TaggitTag = get_model('taggit', 'Tag')

Listing = get_model('procure', 'Listing')
ListingMember = get_model('procure', 'ListingMember')
ListingOpening = get_model('procure', 'ListingOpening')
ListingGallery = get_model('procure', 'ListingGallery')
ListingAttachment = get_model('procure', 'ListingAttachment')
ListingLocation = get_model('procure', 'ListingLocation')
ListingState = get_model('procure', 'ListingState')

Propose = get_model('procure', 'Propose')
Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')
Negotiation = get_model('procure', 'Negotiation')
NegotiationText = get_model('procure', 'NegotiationText')
NegotiationAttachment = get_model('procure', 'NegotiationAttachment')


# NEED
class InquiryItemInline(admin.StackedInline):
    model = InquiryItem


class InquiryLocationInline(admin.StackedInline):
    model = InquiryLocation


class InquiryExtend(admin.ModelAdmin):
    model = Inquiry
    inlines = [InquiryItemInline, InquiryLocationInline, ]
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


admin.site.register(Inquiry, InquiryExtend)

admin.site.unregister(TaggitTag)
admin.site.register(InquiryTag)
admin.site.register(InquiryTagItem)


# LISTING
class ListingOpeningInline(admin.StackedInline):
    model = ListingOpening
    max_num = 7


class ListingLocationInline(admin.StackedInline):
    model = ListingLocation


class ListingMemberInline(admin.StackedInline):
    model = ListingMember


class ListingStateInline(admin.StackedInline):
    model = ListingState


class ListingExtend(admin.ModelAdmin):
    model = Listing
    list_display = ('label', 'state', 'location',)
    inlines = [ListingOpeningInline, ListingMemberInline,
               ListingLocationInline, ListingStateInline, ]


class ListingMemberExtend(admin.ModelAdmin):
    model = ListingMember
    list_display = ('label', 'is_default',)


admin.site.register(Listing, ListingExtend)
admin.site.register(ListingMember, ListingMemberExtend)
admin.site.register(ListingGallery)
admin.site.register(ListingAttachment)


# OFFER
class OfferInline(admin.StackedInline):
    model = Offer


class OfferItemInline(admin.StackedInline):
    model = OfferItem


class ProposeExtend(admin.ModelAdmin):
    model = Propose
    inlines = [OfferInline, ]


class OfferExtend(admin.ModelAdmin):
    model = Offer
    inlines = [OfferItemInline, ]


admin.site.register(Propose, ProposeExtend)
admin.site.register(Offer, OfferExtend)


# NEGOTIATION
class NegotiationTextInline(admin.StackedInline):
    model = NegotiationText


class NegotiationAttachmentInline(admin.StackedInline):
    model = NegotiationAttachment


class NegotiationExtend(admin.ModelAdmin):
    model = Negotiation
    inlines = [NegotiationTextInline, NegotiationAttachmentInline, ]


admin.site.register(Negotiation, NegotiationExtend)
