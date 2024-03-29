from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin import DateFieldListFilter
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
ListingProduct = get_model('procure', 'ListingProduct')
ListingProductAttachment = get_model('procure', 'ListingProductAttachment')
InquirySkip = get_model('procure', 'InquirySkip')

Propose = get_model('procure', 'Propose')
Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')
Negotiation = get_model('procure', 'Negotiation')
NegotiationText = get_model('procure', 'NegotiationText')
NegotiationAttachment = get_model('procure', 'NegotiationAttachment')

Order = get_model('procure', 'Order')
OrderItem = get_model('procure', 'OrderItem')


# NEED
class InquiryItemInline(admin.StackedInline):
    model = InquiryItem
    autocomplete_fields = ('listing',)


class InquiryLocationInline(admin.StackedInline):
    model = InquiryLocation


class InquiryExtend(admin.ModelAdmin):
    model = Inquiry
    inlines = (InquiryItemInline, InquiryLocationInline,)
    readonly_fields = ('tags',)
    list_display = ('keyword', 'user', 'is_open',)
    autocomplete_fields = ('user',)

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


class ListingExtend(admin.ModelAdmin):
    model = Listing
    list_display = ('label', 'status', 'location', 'create_at',)
    list_filter = ('status', ('create_at', DateFieldListFilter), )
    search_fields = ('label', )
    readonly_fields = ('create_at', )
    inlines = [ListingOpeningInline, ListingMemberInline,
               ListingLocationInline, ]


class ListingMemberExtend(admin.ModelAdmin):
    model = ListingMember
    list_display = ('label', 'is_default',)


admin.site.register(Listing, ListingExtend)
admin.site.register(ListingMember, ListingMemberExtend)
admin.site.register(InquirySkip)
admin.site.register(ListingState)
admin.site.register(ListingGallery)
admin.site.register(ListingAttachment)
admin.site.register(ListingProduct)
admin.site.register(ListingProductAttachment)


# OFFER
class OfferInline(admin.StackedInline):
    model = Offer


class OfferItemInline(admin.StackedInline):
    model = OfferItem


class ProposeExtend(admin.ModelAdmin):
    model = Propose
    list_display = ['listing', 'inquiry', 'user', ]
    inlines = [OfferInline, ]


class OfferExtend(admin.ModelAdmin):
    model = Offer
    inlines = [OfferItemInline, ]
    readonly_fields = ['secret', ]


admin.site.register(Propose, ProposeExtend)
admin.site.register(Offer, OfferExtend)
admin.site.register(OfferItem)


# NEGOTIATION
class NegotiationTextInline(admin.StackedInline):
    model = NegotiationText


class NegotiationAttachmentInline(admin.StackedInline):
    model = NegotiationAttachment


class NegotiationExtend(admin.ModelAdmin):
    model = Negotiation
    inlines = [NegotiationTextInline, NegotiationAttachmentInline, ]


admin.site.register(Negotiation, NegotiationExtend)


# ORDER
class OrderItemInline(admin.StackedInline):
    model = OrderItem


class OrderExtend(admin.ModelAdmin):
    model = Order
    inlines = [OrderItemInline, ]


admin.site.register(Order, OrderExtend)
