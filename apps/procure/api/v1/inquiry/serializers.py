import uuid
import math

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Sum
from django.db.models.expressions import Exists, OuterRef
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from rest_framework import serializers
from rest_framework.exceptions import NotFound

from utils.generals import get_model
from ..offer.serializers import RetrieveOfferSerializer

Offer = get_model('procure', 'Offer')
Inquiry = get_model('procure', 'Inquiry')
InquiryItem = get_model('procure', 'InquiryItem')
InquiryLocation = get_model('procure', 'InquiryLocation')
InquirySkip = get_model('procure', 'InquirySkip')
Propose = get_model('procure', 'Propose')
Order = get_model('procure', 'Order')


class _OrderSerializer(serializers.ModelSerializer):
    listing = serializers.CharField(source='propose.listing.label')
    distance = serializers.SerializerMethodField()
    offer_cost = serializers.SerializerMethodField()
    item_additional_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('uuid', 'listing', 'cost', 'description', 'secret',
                  'distance', 'offer_cost', 'item_additional_count',)

    def get_distance(self, instance):
        inquiry_latitude = instance.inquiry.location.latitude
        inquiry_longitude = instance.inquiry.location.longitude

        order_latitude = instance.latitude
        order_longitude = instance.longitude

        calculate_distance = 6371 * math.acos(
            math.cos(math.radians(inquiry_latitude))
            * math.cos(math.radians(order_latitude))
            * math.cos(
                math.radians(order_longitude) - math.radians(inquiry_longitude)
            )
            + math.sin(math.radians(inquiry_latitude))
            * math.sin(math.radians(order_latitude))
        )

        return calculate_distance

    def get_offer_cost(self, instance):
        offer_cost = instance.offer.cost

        if offer_cost > 0:
            return offer_cost
        else:
            item_summary = instance.offer.items.aggregate(
                total_cost=Sum('cost'))
            return item_summary.get('total_cost')

    def get_item_additional_count(self, instance):
        count = instance.offer.items.filter(is_additional=True).count()
        return count


class InquiryListProposeSerializer(serializers.ModelSerializer):
    newest_offer_cost = serializers.IntegerField(read_only=True,
                                                 required=False)
    newest_item_count = serializers.IntegerField(read_only=True)
    newest_item_additional_count = serializers.IntegerField(read_only=True)
    offer_count = serializers.IntegerField(read_only=True, required=False)
    distance = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Propose
        fields = ('uuid', 'create_at', 'listing', 'distance',
                  'newest_offer_cost', 'offer_count',
                  'newest_item_count', 'newest_item_additional_count',)
        depth = 1


class InquiryItemSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    is_delete = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = InquiryItem
        fields = ('uuid', 'label', 'description', 'is_delete',)


class InquiryLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InquiryLocation
        fields = ('latitude', 'longitude')


class BaseInquirySerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    is_offered = serializers.BooleanField(default=False, required=False)
    newest_offer = serializers.SerializerMethodField()
    newest_offer_cost = serializers.IntegerField(required=False)
    newest_item_count = serializers.IntegerField(read_only=True)
    newest_item_additional_count = serializers.IntegerField(read_only=True)
    propose_count = serializers.IntegerField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = InquiryItemSerializer(many=True)
    location = InquiryLocationSerializer()
    distance = serializers.FloatField(required=False)
    order = _OrderSerializer(many=False, read_only=True)

    class Meta:
        model = Inquiry

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context.get('request')

    def get_links(self, instance):
        return {
            'retrieve': self._request.build_absolute_uri(
                reverse('procure_api:inquiry-detail',
                        kwargs={'uuid': instance.uuid})
            ),
            'propose': self._request.build_absolute_uri(
                reverse('procure_api:inquiry-proposes',
                        kwargs={'uuid': instance.uuid})
            ),
            'offer': self._request.build_absolute_uri(
                reverse('procure_api:inquiry-offers',
                        kwargs={'uuid': instance.uuid})
            )
        }

    def get_newest_offer(self, instance):
        """
        Get newest offer from propose
        """
        request = self.context.get('request')
        user = request.user
        user_id = user.id
        default_listing = user.default_listing

        if not default_listing:
            return None

        order = Order.objects.filter(offer_id=OuterRef('id'))
        newest_offers = Offer.objects \
            .prefetch_related('propose', 'propose__listing', 'items__inquiry_item') \
            .select_related('propose') \
            .annotate(is_ordered=Exists(order)) \
            .filter(propose__inquiry_id=instance.id,
                    propose__listing_id=default_listing.id,
                    is_newest=True) \
            .order_by('-create_at')

        if instance.user.id == user_id:
            # by inquiry creator
            newest_offers = newest_offers \
                .filter(propose__inquiry__user_id=request.user.id)
        else:
            # by listing members
            newest_offers = newest_offers \
                .filter(propose__listing__members__user_id=request.user.id)

        newest_offer = newest_offers.first()
        if newest_offer:
            serializer = RetrieveOfferSerializer(newest_offer, many=False,
                                                 context=self.context)
            return serializer.data
        else:
            return None


class CreateInquirySerializer(BaseInquirySerializer):
    class Meta(BaseInquirySerializer.Meta):
        fields = ('user', 'items', 'location', 'keyword', 'is_open',)

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.instance:
            # can't edit if has proposes
            if self.instance.proposes.count() > 0 and data.get('is_open', None) == None:
                raise serializers.ValidationError(
                    {'detail': _("Ada penawaran tidak bisa dirubah")}
                )
        return data

    @transaction.atomic()
    def create(self, validated_data):
        items = validated_data.pop('items', [])
        location = validated_data.pop('location', {})

        # Create instance
        instance = Inquiry.objects.create(**validated_data)

        # Insert inquiry items
        items_instance = [
            InquiryItem(inquiry=instance, **item) for item in items
        ]

        if len(items_instance) > 0:
            InquiryItem.objects.bulk_create(
                items_instance, ignore_conflicts=False)

        # Insert inquiry location
        location = InquiryLocation.objects.create(inquiry=instance, **location)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        items = validated_data.pop('items', [])
        item_mapping = {item.uuid: item for item in instance.items.all()}
        item_data_mapping = {
            item.get('uuid', str(uuid.uuid4())): item for item in items
        }

        item_delete = []
        item_create = []
        item_update = []

        # Mapping
        for uid, data in item_data_mapping.items():
            is_delete = data.get('is_delete', False)

            # current item instance
            item = item_mapping.get(uid, None)

            if is_delete:
                # delete item
                item_delete.append(uid)
            else:
                if item:
                    # update item
                    for k in data:
                        setattr(item, k, data.get(k))
                    item_update.append(item)
                else:
                    # create item
                    # if label same as in current not created
                    if data.get('label') != (item and item.label):
                        obj = InquiryItem(inquiry=instance, **data)
                        item_create.append(obj)

        # Create
        if len(item_create) > 0:
            try:
                InquiryItem.objects.bulk_create(
                    item_create, ignore_conflicts=False)
            except IntegrityError:
                pass

        # Update
        if len(item_update) > 0:
            InquiryItem.objects.bulk_update(
                item_update, ['label', 'description'])

        # Delete
        if len(item_delete) > 0:
            InquiryItem.objects \
                .filter(uuid__in=item_delete, inquiry__user_id=request.user.id) \
                .delete()

        instance.refresh_from_db()
        return super().update(instance, validated_data)


class RetrieveInquirySerializer(BaseInquirySerializer):
    user = serializers.CharField(source='user.name')

    class Meta(BaseInquirySerializer.Meta):
        fields = ('uuid', 'user', 'links', 'create_at', 'keyword',
                  'propose_count', 'items', 'newest_offer',
                  'newest_offer_cost', 'location', 'distance',
                  'newest_item_additional_count', 'is_open', 'order',)


class ListInquirySerializer(BaseInquirySerializer):
    user = serializers.CharField(source='user.name')

    class Meta(BaseInquirySerializer.Meta):
        fields = ('uuid', 'user', 'links', 'create_at', 'keyword',
                  'propose_count', 'items', 'is_offered', 'distance',
                  'newest_offer_cost', 'newest_item_additional_count',
                  'is_open', 'order',)


"""
SKIP...
"""


class CreateInquirySkipSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = InquirySkip
        fields = ('user',)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        try:
            inquiry = Inquiry.objects.get(
                uuid=self.context.get('inquiry_uuid'))
            data.update({'inquiry': inquiry})
        except ObjectDoesNotExist:
            raise NotFound()

        return data

    @transaction.atomic()
    def create(self, validated_data):
        instance, _created = InquirySkip.objects \
            .get_or_create(**validated_data)
        return instance


class RetrieveInquirySkipSerializer(serializers.ModelSerializer):
    inquiry = serializers.UUIDField(source='inquiry.uuid')

    class Meta:
        model = InquirySkip
        fields = '__all__'
