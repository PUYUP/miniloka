import re

from django.db import transaction
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import (
    OuterRef, Exists, Count, Q, F, Sum, Case, When, Value, Subquery,
    IntegerField, FloatField
)

from utils.generals import get_model

Listing = get_model('procure', 'Listing')
ListingLocation = get_model('procure', 'ListingLocation')
ListingState = get_model('procure', 'ListingState')
ListingOpening = get_model('procure', 'ListingOpening')


def extract_hash_tags(s):
    return set(part[1:] for part in s.split() if part.startswith('#'))


@transaction.atomic
def inquiry_save_handler(sender, instance, created, **kwargs):
    # hashtags = list(extract_hash_tags(instance.keyword))
    # tags = ','.join(f'{w}'.format(w) for w in hashtags)
    keyword = getattr(instance, 'keyword', None)
    if keyword:
        tags = keyword.split(' ')
        instance.tags.set(*tags)

    # filter listing by distance from inquiry
    if created:
        latitude = instance.location.latitude
        longitude = instance.location.longitude

        if latitude and longitude:
            keywords = re.split(r"[^A-Za-z']+", keyword) if keyword else []
            keyword_query = Q()

            for keyword in keywords:
                keyword_query |= Q(keyword__icontains=keyword)

            # Calculate distance
            calculate_distance = Value(6371) * ACos(
                Cos(Radians(latitude, output_field=FloatField()))
                * Cos(Radians(F('location__latitude'), output_field=FloatField()))
                * Cos(Radians(F('location__longitude'), output_field=FloatField())
                      - Radians(longitude, output_field=FloatField()))
                + Sin(Radians(latitude, output_field=FloatField()))
                * Sin(Radians(F('location__latitude'), output_field=FloatField())),
                output_field=FloatField()
            )

            # get all listing matching keyword
            listings = Listing.objects \
                .annotate(distance=calculate_distance) \
                .filter(keyword_query, state__status=ListingState.Status.APPROVED,
                        distance__lte=15)


@transaction.atomic()
def listing_member_save_handler(sender, instance, created, **kwargs):
    if instance.is_default == True:
        # Each member can active on one listing
        # member can select default listing
        cls = instance.__class__
        cls.objects \
            .filter(user_id=instance.user.id) \
            .mark_undefault(exclude_uuid=instance.uuid)


@transaction.atomic()
def listing_save_handler(sender, instance, created, **kwargs):
    if created:
        # LOCATION
        if not hasattr(instance, 'location'):
            _instance, _created = ListingLocation.objects \
                .get_or_create(listing=instance)

        # STATE
        if not hasattr(instance, 'state'):
            _instance, _created = ListingState.objects \
                .get_or_create(listing=instance)

        # OPENINGS
        if not instance.openings.exists():
            openings = list()
            days = dict(ListingOpening.Day.choices)
            for day, name in days.items():
                o = ListingOpening(day=day, listing=instance)
                openings.append(o)

            if len(openings) > 0:
                ListingOpening.objects \
                    .bulk_create(openings, ignore_conflicts=False)
