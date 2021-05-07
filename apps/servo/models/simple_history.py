import uuid

from django.db import models
from simple_history import register
from utils.generals import get_model

Need = get_model('servo', 'Need')
NeedItem = get_model('servo', 'NeedItem')
NeedLocation = get_model('servo', 'NeedLocation')

Tag = get_model('servo', 'Tag')
TagItem = get_model('servo', 'TagItem')

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

# NEED
register(Need, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(NeedItem, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(NeedLocation, app=__package__,
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

# OFFER
register(Offer, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(OfferRate, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(OfferItem, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(OfferItemRate, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))
