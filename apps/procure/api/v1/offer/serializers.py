from apps.procure.api.v1.order.serializers import BaseOrderSerializer
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from rest_framework import fields, serializers
from utils.generals import get_model

Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')
Order = get_model('procure', 'Order')
OrderItem = get_model('procure', 'OrderItem')


class OfferItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferItem
        fields = ('uuid', 'inquiry_item', 'label', 'create_at', 'cost', 'discount',
                  'description', 'is_available', 'is_additional',)


class BaseOfferSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    total_item_cost = serializers.IntegerField(read_only=True)
    listing = serializers.CharField(source='propose.listing.label')
    items = OfferItemSerializer(many=True, required=False, read_only=True)
    user = serializers.CharField(source='user.name')
    is_ordered = serializers.BooleanField(default=False, required=False)

    def get_links(self, instance):
        request = self.context.get('request')

        return {
            'retrieve': request.build_absolute_uri(
                reverse('procure_api:offer-detail',
                        kwargs={'uuid': instance.uuid})
            ),
        }

    class Meta:
        model = Offer


"""
READ
"""


class _OrderItemSerializer(serializers.ModelSerializer):
    offer_item = serializers.SlugRelatedField(read_only=True,
                                              slug_field='uuid')

    class Meta:
        model = OrderItem
        fields = '__all__'


class _OrderSerializer(serializers.ModelSerializer):
    items = _OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ('uuid', 'items',)
        depth = 1


class ListOfferSerializer(BaseOfferSerializer):
    class Meta(BaseOfferSerializer.Meta):
        fields = ('can_attend', 'can_attend_radius', 'cost', 'create_at',
                  'discount', 'total_item_cost', 'user',)


class RetrieveOfferSerializer(BaseOfferSerializer):
    order = _OrderSerializer(many=False)

    class Meta(BaseOfferSerializer.Meta):
        fields = ('uuid', 'listing', 'create_at', 'cost', 'discount', 'description',
                  'can_attend', 'can_attend_radius', 'latitude', 'longitude', 'secret',
                  'is_newest', 'items', 'total_item_cost', 'is_ordered', 'order',)
        depth = 1
