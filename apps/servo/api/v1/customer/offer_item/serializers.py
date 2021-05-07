from rest_framework import serializers

from utils.generals import get_model

OfferItem = get_model('servo', 'OfferItem')
OfferItemRate = get_model('servo', 'OfferItemRate')


class OfferItemRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferItemRate
        fields = ('uuid', 'create_at', 'description', 'quantity',
                  'cost', 'discount', 'is_newest')


class OfferItemSerializer(serializers.ModelSerializer):
    item_rates = OfferItemRateSerializer(many=True)
    label = serializers.CharField(source='needitem.label')

    class Meta:
        model = OfferItem
        fields = ('uuid', 'item_rates', 'create_at', 'label', 'needitem',)
        depth = 1
