import uuid

from django.db import models
from simple_history import register
from utils.generals import get_model

Inquiry = get_model('procure', 'Inquiry')
InquiryItem = get_model('procure', 'InquiryItem')
InquiryLocation = get_model('procure', 'InquiryLocation')

Tag = get_model('procure', 'Tag')
TagItem = get_model('procure', 'TagItem')

Listing = get_model('procure', 'Listing')
ListingMember = get_model('procure', 'ListingMember')
ListingOpening = get_model('procure', 'ListingOpening')
ListingGallery = get_model('procure', 'ListingGallery')
ListingAttachment = get_model('procure', 'ListingAttachment')
ListingLocation = get_model('procure', 'ListingLocation')
ListingProduct = get_model('procure', 'ListingProduct')
ListingProductAttachment = get_model('procure', 'ListingProductAttachment')

Propose = get_model('procure', 'Propose')
Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')

Order = get_model('procure', 'Order')
OrderItem = get_model('procure', 'OrderItem')

# NEED
register(Inquiry, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(InquiryItem, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(InquiryLocation, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

# TAG
register(Tag, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(TagItem, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

# LISTING
register(Listing, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(ListingMember, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(ListingOpening, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(ListingGallery, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(ListingAttachment, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(ListingLocation, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(ListingProduct, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(ListingProductAttachment, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

# OFFER
register(Propose, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Offer, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(OfferItem, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

# ORDER
register(Order, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(OrderItem, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))
