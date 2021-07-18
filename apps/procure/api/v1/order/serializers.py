from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from utils.generals import get_model

Order = get_model('procure', 'Order')
OrderItem = get_model('procure', 'OrderItem')
Inquiry = get_model('procure', 'Inquiry')
Propose = get_model('procure', 'Propose')
Offer = get_model('procure', 'Offer')
OfferItem = get_model('procure', 'OfferItem')


class _OfferItemCreateSerializer(serializers.ModelSerializer):
    offer_item = serializers.SlugRelatedField(slug_field='uuid',
                                              queryset=OfferItem.objects.all())

    class Meta:
        model = OrderItem
        fields = ('offer_item',)


class _OfferItemRetrieveSerializer(serializers.ModelSerializer):
    offer_item = serializers.SlugRelatedField(slug_field='uuid',
                                              queryset=OfferItem.objects.all())

    class Meta:
        model = OrderItem
        fields = '__all__'


class BaseOrderSerializer(serializers.ModelSerializer):
    inquiry = serializers.SlugRelatedField(slug_field='uuid',
                                           queryset=Inquiry.objects.all())
    offer = serializers.SlugRelatedField(slug_field='uuid',
                                         queryset=Offer.objects.all())

    class Meta:
        model = Order


class CreateOrderSerializer(BaseOrderSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = _OfferItemCreateSerializer(many=True, allow_empty=False)

    class Meta(BaseOrderSerializer.Meta):
        fields = ('user', 'inquiry', 'offer', 'secret', 'items',
                  'cost', 'description', 'discount',)

    def validate(self, attrs):
        offer = attrs.get('offer') or self.initial_data.get('offer')
        secret = attrs.get('secret') or self.initial_data.get('secret')

        if offer.secret != secret:
            raise serializers.ValidationError({
                'detail': _("Kode rahasia salah")
            })

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        instance, created = Order.objects \
            .get_or_create(**validated_data)

        # check offer_item has in order
        order_item_mapping = {
            str(item.offer_item.uuid): item for item in instance.items.all()
        }

        offer_item_mapping = {
            str(item.get('offer_item').uuid): item.get('offer_item') for item in items_data
        }

        create_order_item = []
        item_fields = ['label', 'cost', 'discount', 'quantity', 'description',
                       'is_available', 'is_additional']

        for offer_item_uuid, data in offer_item_mapping.items():
            order_item = order_item_mapping.get(offer_item_uuid, None)

            # create order_item
            if order_item is None:
                order_item_data = {x: getattr(data, x) for x in item_fields}
                obj = OrderItem(order=instance, offer_item=data,
                                **order_item_data)
                create_order_item.append(obj)

        # Create order item
        if created:
            if len(create_order_item) > 0:
                try:
                    OrderItem.objects.bulk_create(create_order_item,
                                                  ignore_conflicts=False)
                except IntegrityError:
                    pass

        return instance


class RetrieveOrderSerializer(BaseOrderSerializer):
    items = _OfferItemRetrieveSerializer(many=True)
    is_creator = serializers.BooleanField(read_only=True)
    total_cost = serializers.IntegerField(read_only=True)

    class Meta(BaseOrderSerializer.Meta):
        exclude = ('user',)
        depth = 1
