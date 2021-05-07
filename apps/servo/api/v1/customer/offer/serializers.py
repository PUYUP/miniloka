from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from utils.generals import get_model
from ..offer_item.serializers import OfferItemSerializer
from ..offer_rate.serializers import OfferRateSerializer
from ..need.serializers import NeedItemSerializer

Need = get_model('servo', 'Need')
Offer = get_model('servo', 'Offer')
OfferRate = get_model('servo', 'OfferRate')


class CreateOfferSerializer(serializers.ModelSerializer):
    need = serializers.SlugRelatedField(slug_field='uuid', write_only=False,
                                        queryset=Need.objects.all())
    rates = OfferRateSerializer(many=False, required=True)

    class Meta:
        model = Offer
        fields = ('need', 'rates',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rates = None
        self._instance = None
        self._request = self._context.get('request')
        self._members_of = self._request.user.members_of

    @transaction.atomic()
    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        # Get rates and ris_whole_rateve it
        self._rates = data.pop('rates') or self.initial_data.pop('rates')

        # Fake save offer
        self._instance, _created = Offer.objects \
            .get_or_create(listing=self._members_of.listing, **data)

        if self._instance.count_rates > 5:
            raise serializers.ValidationError({'rates': _("Max only 5 times")})
        return data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not self._members_of:
            raise serializers.ValidationError({
                'listing': _("Not registered as member in any Listing")
            })
        return attrs

    @transaction.atomic()
    def create(self, validated_data):
        if self._instance:
            OfferRate.objects \
                .get_or_create(offer=self._instance, **self._rates)
        return self._instance


class BaseOfferSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='servo_api:customer:offer-detail',
                                               lookup_field='uuid', read_only=True)
    rates = OfferRateSerializer(many=True, read_only=True)
    rate_cost = serializers.IntegerField(read_only=True)
    is_whole_rate = serializers.BooleanField()
    rate_distance = serializers.DecimalField(max_digits=5, decimal_places=1)
    rate_latitude = serializers.DecimalField(max_digits=16, decimal_places=9)
    rate_longitude = serializers.DecimalField(max_digits=16, decimal_places=9)
    need_latitude = serializers.DecimalField(max_digits=16, decimal_places=9)
    need_longitude = serializers.DecimalField(max_digits=16, decimal_places=9)


class RetrieveOfferSerializer(BaseOfferSerializer):
    rates = OfferRateSerializer(many=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = ('uuid', 'url', 'create_at', 'listing', 'need', 'rates',
                  'items', 'rate_cost', 'is_whole_rate', 'rate_distance', 'rate_latitude',
                  'rate_longitude', 'need_latitude', 'need_longitude',)
        depth = 1

    def get_items(self, instance):
        if instance.items.exists():
            offer_items = instance.items.all()
            serializer = OfferItemSerializer(offer_items, many=True,
                                             context=self.context)
            return serializer.data
        else:
            items = instance.need.items.all()
            serializer = NeedItemSerializer(items, many=True,
                                            context=self.context)
            return serializer.data


class ListOfferSerializer(BaseOfferSerializer):
    class Meta:
        model = Offer
        fields = ('uuid', 'url', 'create_at', 'listing',
                  'need', 'rates', 'rate_cost', 'rate_distance',)
        depth = 1
