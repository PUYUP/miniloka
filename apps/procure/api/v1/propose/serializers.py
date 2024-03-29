from django.core.exceptions import ObjectDoesNotExist
from django.db.models.expressions import Exists, OuterRef
from apps.procure.api.v1.listing.serializers import ListingLocation
from django.db import transaction
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from rest_framework import serializers
from utils.generals import get_model

from ..offer.serializers import RetrieveOfferSerializer

Inquiry = get_model('procure', 'Inquiry')
InquiryItem = get_model('procure', 'InquiryItem')
Propose = get_model('procure', 'Propose')
Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')
Listing = get_model('procure', 'Listing')
Order = get_model('procure', 'Order')


class BaseProposeSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self._context.get('request')

    def get_links(self, instance):
        latest_offer = instance.latest_offer()

        ret = {
            'retrieve': self._request.build_absolute_uri(
                reverse('procure_api:propose-detail',
                        kwargs={'uuid': instance.uuid})
            ),
            'offer': self._request.build_absolute_uri(
                reverse('procure_api:propose-offers',
                        kwargs={'uuid': instance.uuid})
            ),
        }

        if latest_offer and hasattr(latest_offer, 'order'):
            order = getattr(latest_offer, 'order')
            if order:
                uri = self._request.build_absolute_uri(
                    reverse(
                        'procure_api:order-detail',
                        kwargs={'uuid': order.uuid}
                    )
                )
                ret.update({'order': uri})
        return ret


"""
CREATE
"""


class _Coordinate(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class _OfferItemSerializer(serializers.Serializer):
    inquiry_item = serializers.SlugRelatedField(slug_field='uuid', required=False,
                                                queryset=InquiryItem.objects.all())
    label = serializers.CharField(required=False)
    cost = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_available = serializers.BooleanField(default=False)


class _OfferSerializer(serializers.Serializer):
    cost = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    can_attend = serializers.BooleanField(default=True)


class CreateProposeSerializer(BaseProposeSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    listing = serializers.SlugRelatedField(slug_field='uuid',
                                           queryset=Listing.objects.all())
    inquiry = serializers.SlugRelatedField(slug_field='uuid',
                                           queryset=Inquiry.objects.all())

    # Custom fields
    coordinate = _Coordinate(many=False, write_only=True, required=False)
    offer = _OfferSerializer(many=False, write_only=True, required=False)
    offer_items = _OfferItemSerializer(many=True, write_only=True,
                                       required=True, allow_empty=False)

    class Meta:
        model = Propose
        fields = ('user', 'listing', 'inquiry',
                  'coordinate', 'offer', 'offer_items',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context.get('request')

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.instance:
            listing = data.get('listing')
            inquiry = data.get('inquiry')

            try:
                propose = Propose.objects.get(listing=listing, inquiry=inquiry)
            except ObjectDoesNotExist:
                propose = None

            if propose:
                latest_offer = propose.latest_offer()
                order = getattr(latest_offer, 'order', None)

                if order:
                    raise serializers.ValidationError({
                        'detail': _("Konsumen menerima tawaran tidak bisa dirubah.")
                    })
        return data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        listing_instance = data.get('listing')

        # listing must approved
        if listing_instance.status == listing_instance.Status.PENDING:
            raise serializers.ValidationError({
                'detail': _("Bisnis sedang diverifikasi tidak bisa mengirim penawaran.")
            })

        # restric members only
        members = listing_instance.members \
            .filter(user_id=self._request.user.id, is_allow_propose=True)

        if not members.exists():
            raise serializers.ValidationError({
                'detail': _("Tindakan ditolak. Anda tidak terdaftar dalam bisnis ini.")
            })
        return data

    @transaction.atomic
    def create(self, validated_data):
        offer_data = validated_data.pop('offer', dict())
        offer_cost = offer_data.pop('cost', 0)
        offer_items_data = validated_data.pop('offer_items', list())
        coordinate_data = validated_data.pop('coordinate', dict())
        listing_instance = validated_data.get('listing')

        # Ignore user
        user = validated_data.pop('user')
        defaults = {'user': user}

        # Create or get propose
        instance, _created = Propose.objects \
            .get_or_create(defaults=defaults, **validated_data)

        # Get coordinate from listing if not provided from request
        if not coordinate_data:
            coordinate_data = {
                'latitude': listing_instance.location.latitude,
                'longitude': listing_instance.location.longitude,
            }

        # Create Offer
        offer_instance = Offer.objects \
            .create(
                propose=instance,
                user_id=self._request.user.id,
                cost=offer_cost,
                **coordinate_data,
                **offer_data
            )

        # Get unlisted in offer_items inquiry items
        inquiry_items_uuid = [
            item.get('inquiry_item').uuid if item.get('inquiry_item') else None for item in offer_items_data
        ]

        inquiry_items_unlisted = instance.inquiry.items \
            .exclude(uuid__in=inquiry_items_uuid)

        # Insert inquiry_items to offer to
        if inquiry_items_unlisted.exists():
            for item in inquiry_items_unlisted:
                item_data = {'inquiry_item': item, 'cost': 0}
                offer_items_data.append(item_data)

        # Create Offer Items
        # prepare bulk create
        bulk_create_offer_items = []
        for item in offer_items_data:
            inquiry_item = item.get('inquiry_item', None)
            if inquiry_item is None:
                item.update({'is_additional': True})

            item_cost = item.pop('cost', 0)
            cost = 0 if offer_cost > 0 else item_cost
            item_obj = OfferItem(offer=offer_instance, user=self._request.user,
                                 cost=cost, **item)
            bulk_create_offer_items.append(item_obj)

        if len(bulk_create_offer_items) > 0:
            OfferItem.objects.bulk_create(bulk_create_offer_items,
                                          ignore_conflicts=False)
        return instance


"""
READ
"""


class ListProposeSerializer(BaseProposeSerializer):
    class Meta:
        model = Propose
        fields = ('uuid', 'links', 'create_at', 'listing', 'inquiry',)
        depth = 1


class _ProposeListingLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingLocation
        exclude = ('listing',)


class _ProposeListingSerializer(serializers.ModelSerializer):
    location = _ProposeListingLocationSerializer(many=False)

    class Meta:
        model = Listing
        fields = '__all__'
        depth = 1


class RetrieveProposeSerializer(BaseProposeSerializer):
    inquiry = serializers.UUIDField(source='inquiry.uuid', required=False)
    listing = _ProposeListingSerializer(many=False, required=False)
    newest_offer = serializers.SerializerMethodField()
    has_order = serializers.SerializerMethodField()

    class Meta:
        model = Propose
        fields = ('uuid', 'create_at', 'update_at',
                  'links', 'newest_offer', 'listing',
                  'inquiry', 'has_order',)
        depth = 1

    def get_newest_offer(self, instance):
        """
        Get newest offer from propose
        """
        order = Order.objects.filter(offer_id=OuterRef('id'))
        newest_offer = Offer.objects \
            .prefetch_related('items', 'items__inquiry_item', 'propose', 'user') \
            .select_related('propose', 'user') \
            .annotate(
                is_ordered=Exists(order),
                total_item_cost=Sum('items__cost')
            ) \
            .filter(propose_id=instance.id, is_newest=True) \
            .order_by('-create_at') \
            .first()

        if newest_offer:
            serializer = RetrieveOfferSerializer(newest_offer, many=False,
                                                 context=self.context)
            return serializer.data
        else:
            return None

    def get_has_order(self, instance):
        return hasattr(instance.inquiry, 'order')
