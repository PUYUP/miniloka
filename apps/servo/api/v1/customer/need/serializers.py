from django.db import transaction
from django.urls import reverse
from django.utils.http import urlencode

from rest_framework import serializers

from utils.generals import get_model
from apps.servo.api.utils import DynamicFieldsModelSerializer

Need = get_model('servo', 'Need')
NeedItem = get_model('servo', 'NeedItem')
NeedLocation = get_model('servo', 'NeedLocation')


class NeedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeedItem
        fields = ('uuid', 'label', 'description')


class NeedLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeedLocation
        fields = ('latitude', 'longitude')


class BaseNeedSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='servo_api:customer:need-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = NeedItemSerializer(many=True, required=False)
    location = NeedLocationSerializer()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context.get('request')


class CreateNeedSerializer(BaseNeedSerializer):
    class Meta:
        model = Need
        fields = ('user', 'items', 'location', 'variety', 'description',)

    @transaction.atomic()
    def create(self, validated_data):
        needitems_data = validated_data.pop('items', [])
        location = validated_data.pop('location', {})

        # Create instance
        instance = Need.objects.create(**validated_data)

        # Insert need items
        needitems_instance = []
        for needitem in needitems_data:
            item = NeedItem(need=instance, **needitem)
            needitems_instance.append(item)

        if len(needitems_instance) > 0:
            NeedItem.objects.bulk_create(needitems_instance,
                                         ignore_conflicts=False)

        # Insert need location
        NeedLocation.objects.create(need=instance, **location)
        return instance


class RetrieveNeedSerializer(BaseNeedSerializer):
    url_offers = serializers.SerializerMethodField(read_only=True)
    variety_label = serializers.CharField(read_only=True)
    total_offer = serializers.IntegerField(read_only=True)

    class Meta:
        model = Need
        fields = ('uuid', 'url_offers', 'create_at', 'description',
                  'variety_label', 'total_offer', 'items', 'location')

    def get_url_offers(self, instance):
        url = reverse('servo_api:customer:offer-list')
        uri = self._request.build_absolute_uri(url)
        return '{}?{}'.format(uri, urlencode({'need_uuid': instance.uuid}))


class ListNeedSerializer(RetrieveNeedSerializer, DynamicFieldsModelSerializer):
    class Meta:
        model = Need
        fields = ('uuid', 'url', 'url_offers', 'create_at', 'description',
                  'variety_label', 'total_offer', 'items')
