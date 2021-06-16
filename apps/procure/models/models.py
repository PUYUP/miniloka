from .inquiry import *
from .listing import *
from .propose import *
from utils.generals import is_model_registered

__all__ = list()

# 1
if not is_model_registered('procure', 'Inquiry'):
    class Inquiry(AbstractInquiry):
        class Meta(AbstractInquiry.Meta):
            pass

    __all__.append('Inquiry')


# 2
if not is_model_registered('procure', 'InquiryItem'):
    class InquiryItem(AbstractInquiryItem):
        class Meta(AbstractInquiryItem.Meta):
            pass

    __all__.append('InquiryItem')


# 3
if not is_model_registered('procure', 'InquiryItemAttachment'):
    class InquiryItemAttachment(AbstractInquiryItemAttachment):
        class Meta(AbstractInquiryItemAttachment.Meta):
            pass

    __all__.append('InquiryItemAttachment')


# 4
if not is_model_registered('procure', 'InquiryLocation'):
    class InquiryLocation(AbstractInquiryLocation):
        class Meta(AbstractInquiryLocation.Meta):
            pass

    __all__.append('InquiryLocation')


# 5
if not is_model_registered('procure', 'Listing'):
    class Listing(AbstractListing):
        class Meta(AbstractListing.Meta):
            pass

    __all__.append('Listing')


# 6
if not is_model_registered('procure', 'ListingState'):
    class ListingState(AbstractListingState):
        class Meta(AbstractListingState.Meta):
            pass

    __all__.append('ListingState')


# 7
if not is_model_registered('procure', 'ListingMember'):
    class ListingMember(AbstractListingMember):
        class Meta(AbstractListingMember.Meta):
            pass

    __all__.append('ListingMember')


# 8
if not is_model_registered('procure', 'ListingOpening'):
    class ListingOpening(AbstractListingOpening):
        class Meta(AbstractListingOpening.Meta):
            pass

    __all__.append('ListingOpening')


# 9
if not is_model_registered('procure', 'ListingGallery'):
    class ListingGallery(AbstractListingGallery):
        class Meta(AbstractListingGallery.Meta):
            pass

    __all__.append('ListingGallery')


# 10
if not is_model_registered('procure', 'ListingAttachment'):
    class ListingAttachment(AbstractListingAttachment):
        class Meta(AbstractListingAttachment.Meta):
            pass

    __all__.append('ListingAttachment')


# 11
if not is_model_registered('procure', 'ListingLocation'):
    class ListingLocation(AbstractListingLocation):
        class Meta(AbstractListingLocation.Meta):
            pass

    __all__.append('ListingLocation')


# 12
if not is_model_registered('procure', 'Propose'):
    class Propose(AbstractPropose):
        class Meta(AbstractPropose.Meta):
            pass

    __all__.append('Propose')


# 13
if not is_model_registered('procure', 'Offer'):
    class Offer(AbstractOffer):
        class Meta(AbstractOffer.Meta):
            pass

    __all__.append('Offer')


# 14
if not is_model_registered('procure', 'OfferItem'):
    class OfferItem(AbstractOfferItem):
        class Meta(AbstractOfferItem.Meta):
            pass

    __all__.append('OfferItem')


# 15
if not is_model_registered('procure', 'Negotiation'):
    class Negotiation(AbstractNegotiation):
        class Meta(AbstractNegotiation.Meta):
            pass

    __all__.append('Negotiation')


# 16
if not is_model_registered('procure', 'NegotiationText'):
    class NegotiationText(AbstractNegotiationText):
        class Meta(AbstractNegotiationText.Meta):
            pass

    __all__.append('NegotiationText')


# 17
if not is_model_registered('procure', 'NegotiationAttachment'):
    class NegotiationAttachment(AbstractNegotiationAttachment):
        class Meta(AbstractNegotiationAttachment.Meta):
            pass

    __all__.append('NegotiationAttachment')
