from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from rest_framework import serializers
from utils.generals import get_model

Inquiry = get_model('procure', 'Inquiry')
InquiryItem = get_model('procure', 'InquiryItem')
Propose = get_model('procure', 'Propose')
Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')
Listing = get_model('procure', 'Listing')


class BaseProposeSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self._context.get('request')

    def get_links(self, instance):
        return {
            'retrieve': self._request.build_absolute_uri(
                reverse('procure_api:propose-detail',
                        kwargs={'uuid': instance.uuid})
            ),
            'offer': self._request.build_absolute_uri(
                reverse('procure_api:propose-offers',
                        kwargs={'uuid': instance.uuid})
            )
        }


"""
CREATE
"""


class _Coordinate(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class _OffersSerializer(serializers.Serializer):
    inquiry_item = serializers.SlugRelatedField(slug_field='uuid',
                                                queryset=InquiryItem.objects.all())
    cost = serializers.IntegerField(required=True)


class _OfferSerializer(serializers.Serializer):
    cost = serializers.IntegerField(required=True)


class CreateProposeSerializer(BaseProposeSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    listing = serializers.SlugRelatedField(slug_field='uuid',
                                           queryset=Listing.objects.all())
    inquiry = serializers.SlugRelatedField(slug_field='uuid',
                                           queryset=Inquiry.objects.all())

    # Custom fields
    coordinate = _Coordinate(many=False, write_only=True)
    offer = _OfferSerializer(many=False, write_only=True, required=False)
    offer_items = _OffersSerializer(many=True, write_only=True,
                                    required=True, allow_empty=False)

    class Meta:
        model = Propose
        fields = ('user', 'listing', 'inquiry',
                  'coordinate', 'offer', 'offer_items',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context.get('request')

    @transaction.atomic
    def create(self, validated_data):
        offer_data = validated_data.pop('offer', dict())
        offer_items_data = validated_data.pop('offer_items', list())
        coodinate_data = validated_data.pop('coordinate', dict())

        # Create or get propose
        instance, _created = Propose.objects.get_or_create(**validated_data)

        # Create Offer
        offer_instance = Offer.objects.create(propose=instance,
                                              user_id=self._request.user.id,
                                              cost=offer_data.get('cost', 0),
                                              **coodinate_data)

        # Get unlisted in offer_items inquiry items
        inquiry_items_uuid = [
            item.get('inquiry_item').uuid for item in offer_items_data
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
            item_cost = item.pop('cost', 0)
            cost = 0 if offer_data.get('cost', 0) > 0 else item_cost
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


class RetrieveProposeSerializer(BaseProposeSerializer):
    class Meta:
        model = Propose
        fields = ('uuid', 'create_at', 'update_at',
                  'listing', 'inquiry', 'links',)
        depth = 1
