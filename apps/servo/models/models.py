from .need import *
from .listing import *
from .offer import *
from utils.generals import is_model_registered

__all__ = list()

# 1
if not is_model_registered('servo', 'Need'):
    class Need(AbstractNeed):
        class Meta(AbstractNeed.Meta):
            pass

    __all__.append('Need')


# 2
if not is_model_registered('servo', 'NeedItem'):
    class NeedItem(AbstractNeedItem):
        class Meta(AbstractNeedItem.Meta):
            pass

    __all__.append('NeedItem')


# 3
if not is_model_registered('servo', 'NeedItemAttachment'):
    class NeedItemAttachment(AbstractNeedItemAttachment):
        class Meta(AbstractNeedItemAttachment.Meta):
            pass

    __all__.append('NeedItemAttachment')


# 4
if not is_model_registered('servo', 'NeedLocation'):
    class NeedLocation(AbstractNeedLocation):
        class Meta(AbstractNeedLocation.Meta):
            pass

    __all__.append('NeedLocation')


# 5
if not is_model_registered('servo', 'Listing'):
    class Listing(AbstractListing):
        class Meta(AbstractListing.Meta):
            pass

    __all__.append('Listing')


# 6
if not is_model_registered('servo', 'ListingMember'):
    class ListingMember(AbstractListingMember):
        class Meta(AbstractListingMember.Meta):
            pass

    __all__.append('ListingMember')


# 7
if not is_model_registered('servo', 'ListingOpening'):
    class ListingOpening(AbstractListingOpening):
        class Meta(AbstractListingOpening.Meta):
            pass

    __all__.append('ListingOpening')


# 8
if not is_model_registered('servo', 'ListingGallery'):
    class ListingGallery(AbstractListingGallery):
        class Meta(AbstractListingGallery.Meta):
            pass

    __all__.append('ListingGallery')


# 9
if not is_model_registered('servo', 'ListingAttachment'):
    class ListingAttachment(AbstractListingAttachment):
        class Meta(AbstractListingAttachment.Meta):
            pass

    __all__.append('ListingAttachment')


# 10
if not is_model_registered('servo', 'ListingLocation'):
    class ListingLocation(AbstractListingLocation):
        class Meta(AbstractListingLocation.Meta):
            pass

    __all__.append('ListingLocation')


# 11
if not is_model_registered('servo', 'Offer'):
    class Offer(AbstractOffer):
        class Meta(AbstractOffer.Meta):
            pass

    __all__.append('Offer')


# 12
if not is_model_registered('servo', 'OfferRate'):
    class OfferRate(AbstractOfferRate):
        class Meta(AbstractOfferRate.Meta):
            pass

    __all__.append('OfferRate')


# 13
if not is_model_registered('servo', 'OfferItem'):
    class OfferItem(AbstractOfferItem):
        class Meta(AbstractOfferItem.Meta):
            pass

    __all__.append('OfferItem')

# 14
if not is_model_registered('servo', 'OfferItemRate'):
    class OfferItemRate(AbstractOfferItemRate):
        class Meta(AbstractOfferItemRate.Meta):
            pass

    __all__.append('OfferItemRate')


# 15
if not is_model_registered('servo', 'OfferDiscussion'):
    class OfferDiscussion(AbstractOfferDiscussion):
        class Meta(AbstractOfferDiscussion.Meta):
            pass

    __all__.append('OfferDiscussion')


# 16
if not is_model_registered('servo', 'OfferDiscussionText'):
    class OfferDiscussionText(AbstractOfferDiscussionText):
        class Meta(AbstractOfferDiscussionText.Meta):
            pass

    __all__.append('OfferDiscussionText')

# 17
if not is_model_registered('servo', 'OfferDiscussionAttachment'):
    class OfferDiscussionAttachment(AbstractOfferDiscussionAttachment):
        class Meta(AbstractOfferDiscussionAttachment.Meta):
            pass

    __all__.append('OfferDiscussionAttachment')
