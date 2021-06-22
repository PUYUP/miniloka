
import re

from django.conf import settings
from django.db import transaction
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import Q, F, Value, FloatField
from django.db.models.expressions import OuterRef, Subquery

from utils.generals import get_model
from .tasks import send_inquiry_notification

Listing = get_model('procure', 'Listing')
ListingLocation = get_model('procure', 'ListingLocation')
ListingState = get_model('procure', 'ListingState')
ListingOpening = get_model('procure', 'ListingOpening')
ListingMember = get_model('procure', 'ListingMember')
UserMeta = get_model('person', 'UserMeta')


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


@transaction.atomic
def inquiry_location_save_handler(sender, instance, created, **kwargs):
    inquiry = instance.inquiry
    keyword = inquiry.keyword

    # filter listing by distance from inquiry
    if not created:
        latitude = instance.latitude
        longitude = instance.longitude

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
            # except listing from creator
            listing_ids = Listing.objects \
                .annotate(distance=calculate_distance) \
                .filter(keyword_query, state__status=ListingState.Status.APPROVED) \
                .exclude(members__user__id=inquiry.user.id) \
                .values_list('id', flat=True)

            user_meta_fcm_token = UserMeta.objects \
                .prefetch_related('user') \
                .select_related('user') \
                .filter(user_id=OuterRef('user__id'), meta_key='fcm_token')

            member_fcm_tokens = ListingMember.objects \
                .prefetch_related('listing', 'user') \
                .select_related('listing', 'user') \
                .annotate(fcm_token=Subquery(
                    user_meta_fcm_token.values('meta_value')[:1])) \
                .filter(listing_id__in=listing_ids, fcm_token__isnull=False,
                        is_allow_offer=True, is_allow_propose=True) \
                .distinct() \
                .values_list('fcm_token', flat=True)

            context = {
                'fcm_tokens': list(member_fcm_tokens),
                'inquiry_user': inquiry.user.name,
                'inquiry_keyword': keyword,
            }

            if member_fcm_tokens.exists():
                # send_inquiry_notification.delay(context)  # with celery
                # send_inquiry_notification(context)  # without celery
                pass


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
