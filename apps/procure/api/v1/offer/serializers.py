from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from rest_framework import fields, serializers
from utils.generals import get_model

Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')


class OfferItemSerializer(serializers.ModelSerializer):
    inquiry_item = serializers.CharField(source='inquiry_item.label',
                                         read_only=True)

    class Meta:
        model = OfferItem
        fields = ('uuid', 'create_at', 'cost', 'discount',
                  'description', 'inquiry_item',)


class BaseOfferSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    total_item_cost = serializers.IntegerField(read_only=True)
    listing = serializers.CharField(source='propose.listing.label')
    items = OfferItemSerializer(many=True, required=False, read_only=True)
    user = serializers.CharField(source='user.name')

    def get_links(self, instance):
        request = self.context.get('request')

        return {
            'retrieve': request.build_absolute_uri(
                reverse('procure_api:offer-detail',
                        kwargs={'uuid': instance.uuid})
            ),
        }


"""
READ
"""


class ListOfferSerializer(BaseOfferSerializer):
    class Meta:
        model = Offer
        fields = ('can_attend', 'can_attend_radius', 'cost', 'create_at',
                  'discount', 'total_item_cost', 'user',)


class RetrieveOfferSerializer(BaseOfferSerializer):
    class Meta:
        model = Offer
        fields = ('uuid', 'listing', 'create_at', 'cost', 'discount', 'description',
                  'can_attend', 'can_attend_radius', 'latitude', 'longitude',
                  'is_newest', 'items', 'total_item_cost',)
        depth = 1
