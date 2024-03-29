import re

from django.conf import settings
from django.db import transaction
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import Q, F, Value, FloatField
from django.db.models.expressions import OuterRef, Subquery
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from utils.generals import get_model
from apps.procure import settings as procure_settings
from .tasks import (
    send_fcm_notification,
    send_inquiry_notification,
    send_offer_notification,
    send_order_notification
)

Listing = get_model('procure', 'Listing')
ListingLocation = get_model('procure', 'ListingLocation')
ListingState = get_model('procure', 'ListingState')
ListingOpening = get_model('procure', 'ListingOpening')
ListingMember = get_model('procure', 'ListingMember')
UserMeta = get_model('person', 'UserMeta')
Notification = get_model('notifier', 'Notification')

DISTANCE_RADIUS = procure_settings.DISTANCE_RADIUS
UserModel = get_user_model()


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
    if created:
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
            listing_intances = Listing.objects \
                .annotate(distance=calculate_distance) \
                .filter(keyword_query, status=Listing.Status.APPROVED,
                        distance__lte=DISTANCE_RADIUS) \
                .exclude(members__user_id=inquiry.user.id) \

            listing_ids = listing_intances.values_list('id', flat=True)

            # get user fcm tokens
            user_meta_fcm_token = UserMeta.objects \
                .prefetch_related('user') \
                .select_related('user') \
                .filter(user_id=OuterRef('user__id'), meta_key='fcm_token')

            # listing members
            listing_members = ListingMember.objects \
                .prefetch_related('listing', 'user') \
                .select_related('listing', 'user') \
                .filter(
                    listing_id__in=listing_ids,
                    is_allow_offer=True,
                    is_allow_propose=True
                )

            # fcm token from listing members
            member_fcm_tokens = listing_members \
                .annotate(
                    fcm_token=Subquery(
                        user_meta_fcm_token.values('meta_value')[:1]
                    )
                ) \
                .filter(fcm_token__isnull=False) \
                .values_list('fcm_token', flat=True) \
                .distinct()

            # send notifications
            if listing_members.exists():
                recipients_id = listing_members \
                    .values_list('user_id', flat=True)

                recipients_user = UserModel.objects \
                    .filter(id__in=recipients_id) \
                    .values_list('id', flat=True)

                notifier_context = {
                    'actor': inquiry.user.id,
                    'recipient': list(recipients_user),
                    'action_object': inquiry.id,
                    'target': list(listing_ids),
                    'verb': _("mengirim permintaan"),
                    'data': {
                        'obtain': 'inquiry'
                    }
                }

                if settings.DEBUG:
                    transaction.on_commit(
                        lambda: send_inquiry_notification(**notifier_context))  # without celery
                else:
                    transaction.on_commit(
                        lambda: send_inquiry_notification.delay(**notifier_context))  # with celery

            fcm_context = {
                'fcm_tokens': list(member_fcm_tokens),
                'inquiry_user': inquiry.user.name,
                'inquiry_keyword': keyword,
            }

            if member_fcm_tokens.exists():
                if settings.DEBUG:
                    transaction.on_commit(
                        lambda: send_fcm_notification(**fcm_context))  # without celery
                else:
                    transaction.on_commit(
                        lambda: send_fcm_notification.delay(**fcm_context))  # with celery


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
            _location, _created = ListingLocation.objects \
                .get_or_create(listing=instance)

        # STATE
        _states, _created = ListingState.objects \
            .get_or_create(listing=instance, status=instance.status)

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


@transaction.atomic()
def offer_save_handler(sender, instance, created, **kwargs):
    if created:
        notifier_context = {
            'actor': instance.user.id,
            'recipient': instance.propose.inquiry.user.id,
            'action_object': instance.id,
            'target': instance.propose.inquiry.id,
            'verb': _("memberi penawaran"),
            'data': {
                'obtain': 'offer'
            }
        }

        Notification.objects \
            .mark_as_read(
                recipient=instance.propose.inquiry.user,
                actor_object_id=instance.user.id,
                target_object_id=instance.propose.inquiry.id
            )

        if settings.DEBUG:
            transaction.on_commit(
                lambda: send_offer_notification(**notifier_context))  # without celery
        else:
            transaction.on_commit(
                lambda: send_offer_notification.delay(**notifier_context))  # with celery


@transaction.atomic()
def inquiry_skip_save_handler(sender, instance, created, **kwargs):
    if created:
        default_listing = instance.user.default_listing

        Notification.objects \
            .mark_as_read(
                recipient=instance.user,
                actor_object_id=instance.inquiry.user.id,
                target_object_id=default_listing.id,
                action_object_id=instance.inquiry.id
            )


@transaction.atomic()
def order_save_handler(sender, instance, created, **kwargs):
    if created:
        notifier_context = {
            'actor': instance.user.id,
            'recipient': instance.offer.user.id,
            'action_object': instance.id,
            'target': instance.offer.id,
            'verb': _("menerima penawaran"),
            'data': {
                'obtain': 'order'
            }
        }

        if settings.DEBUG:
            transaction.on_commit(
                lambda: send_order_notification(**notifier_context))  # without celery
        else:
            transaction.on_commit(
                lambda: send_order_notification.delay(**notifier_context))  # with celery
