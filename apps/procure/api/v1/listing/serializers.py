from apps.person.api.v1.profile.serializers import ProfileSerializer
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from utils.generals import get_model

Listing = get_model('procure', 'Listing')
ListingMember = get_model('procure', 'ListingMember')
ListingLocation = get_model('procure', 'ListingLocation')
ListingOpening = get_model('procure', 'ListingOpening')
ListingState = get_model('procure', 'ListingState')

UserModel = get_user_model()


"""
STATE
"""


class BaseStateSerializer(serializers.ModelSerializer):
    pass


"""
LOCATION...
"""


class BaseLocationSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        request = self.context.get('request')

        return {
            'retrieve': request.build_absolute_uri(
                reverse('procure_api:listing-location',
                        kwargs={'uuid': instance.uuid})
            ),
        }


class RetrieveListingLocationSerializer(BaseLocationSerializer):
    listing = serializers.UUIDField(source='listing.uuid')

    class Meta:
        model = ListingLocation
        fields = '__all__'


class UpdateListingLocationSerializer(BaseLocationSerializer):
    class Meta:
        model = ListingLocation
        fields = (
            'street_address',
            'administrative_area_level_1',
            'administrative_area_level_2',
            'administrative_area_level_3',
            'administrative_area_level_4',
            'postal_code',
            'latitude',
            'longitude'
        )
        extra_kwargs = {
            'administrative_area_level_1': {'required': True},
            'administrative_area_level_2': {'required': True},
            'administrative_area_level_3': {'required': True},
            'administrative_area_level_4': {'required': True},
            'postal_code': {'required': True},
            'latitude': {'required': True},
            'longitude': {'required': True}
        }


"""
OPENINGS...
"""


class BaseListingOpeningSerializer(serializers.ModelSerializer):
    pass


class ListingOpeningListSerializer(serializers.ListSerializer):
    @transaction.atomic()
    def update(self, instance, validated_data):
        listing = self.context.get('listing', None)
        request = self.context.get('request', None)

        # Maps for id->instance and id->data item.
        opening_mapping = {opening.uuid: opening for opening in instance}

        used_mapping = []
        deleted_mapping = []

        for data in validated_data:
            is_delete = data.pop('is_delete', False)
            if is_delete:
                deleted_mapping.append(data)
            else:
                used_mapping.append(data)

        # Perform creations and updates.
        ret = []
        for data in used_mapping:
            opening = opening_mapping.get(data.get('uuid'), None)

            # insert listing instance
            data.update({'listing': listing})

            if opening is None:
                ret.append(self.child.create(data))
            else:
                ret.append(self.child.update(opening, data))

        # Perform deletions.
        if len(deleted_mapping) > 0:
            uuids = [data.get('uuid', None) for data in deleted_mapping]
            instance.model.objects \
                .filter(uuid__in=uuids, listing__members__user_id=request.user.id) \
                .delete()
        return ret


class CreateListingOpeningSerializer(BaseListingOpeningSerializer):
    uuid = serializers.UUIDField(required=False)

    # custom field, not model part
    is_delete = serializers.BooleanField(required=False)

    class Meta:
        model = ListingOpening
        fields = ('uuid', 'day', 'open_time',
                  'close_time', 'is_open', 'is_delete',)
        list_serializer_class = ListingOpeningListSerializer

    @transaction.atomic()
    def create(self, validated_data):
        listing = self.context.get('listing', None)

        defaults = {
            'open_time': validated_data.pop('open_time', '00:00'),
            'close_time': validated_data.pop('close_time', '00:00'),
            'is_open': validated_data.pop('is_open', False),
        }

        instance, _created = ListingOpening.objects \
            .update_or_create(listing=listing, defaults=defaults, **validated_data)
        return instance


class RetrieveListingOpeningSerializer(BaseListingOpeningSerializer):
    name = serializers.CharField()

    class Meta:
        model = ListingOpening
        fields = '__all__'


"""
MEMBERS...
"""


class BaseListingMemberSerializer(serializers.ModelSerializer):
    pass


class CreateListingMemberSerializer(BaseListingMemberSerializer):
    user = serializers.SlugRelatedField(slug_field='email',
                                        queryset=UserModel.objects.all())

    class Meta:
        model = ListingMember
        fields = ('user', 'is_admin', 'is_allow_propose',)
        extra_kwargs = {
            'is_admin': {'required': True},
            'is_allow_propose': {'required': True},
        }

    @transaction.atomic()
    def create(self, validated_data):
        listing = self.context.get('listing', None)

        defaults = {
            'is_admin': validated_data.pop('is_admin', False),
            'is_allow_propose': validated_data.pop('is_allow_propose', False),
        }

        instance, _created = ListingMember.objects \
            .update_or_create(listing=listing, defaults=defaults, **validated_data)
        return instance


class RetrieveListingMemberSerializer(BaseListingMemberSerializer):
    profile = ProfileSerializer(source='user.profile')
    user_uuid = serializers.UUIDField(source='user.uuid')

    class Meta:
        model = ListingMember
        fields = ('uuid', 'user', 'user_uuid', 'profile', 'is_creator', 'is_admin',
                  'is_allow_propose', 'is_default',)


"""
LISTING...
"""


class BaseListingSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    location = RetrieveListingLocationSerializer(many=False, read_only=True)
    status_display = serializers.CharField(source='get_status_display',
                                           read_only=True)
    openings = RetrieveListingOpeningSerializer(many=True, read_only=True)
    members = RetrieveListingMemberSerializer(many=True, read_only=True)
    distance = serializers.FloatField(required=False, read_only=True)
    notification_count = serializers.IntegerField(read_only=True)

    def get_links(self, instance):
        request = self.context.get('request')

        return {
            'retrieve': request.build_absolute_uri(
                reverse('procure_api:listing-detail',
                        kwargs={'uuid': instance.uuid})
            ),
            'product': request.build_absolute_uri(
                reverse('procure_api:listing-product',
                        kwargs={'uuid': instance.uuid})
            ),
        }


class CreateListingSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Listing
        fields = ('user', 'label', 'keyword', 'description', 'contact',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context.get('request')
        self._user = None

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        self._user = data.pop('user', None)  \
            or self.initial_data.pop('user', None)

        return data

    @transaction.atomic()
    def create(self, validated_data):
        instance, created = Listing.objects \
            .filter(members__user_id=self._user.id) \
            .get_or_create(**validated_data)

        if instance and created:
            ListingMember.objects \
                .create(user_id=self._user.id, listing_id=instance.id,
                        is_creator=True, is_allow_propose=True,
                        is_allow_offer=True,  is_admin=True,
                        is_default=True)
        return instance


class ListListingSerializer(BaseListingSerializer):
    class Meta:
        model = Listing
        fields = ('uuid', 'links', 'label', 'keyword', 'description', 'create_at',
                  'location', 'status', 'status_display', 'distance',
                  'notification_count',)
        depth = 1


class RetrieveListingSerializer(BaseListingSerializer):
    is_admin = serializers.BooleanField(read_only=True)
    is_creator = serializers.BooleanField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)

    class Meta:
        model = Listing
        fields = ('uuid', 'links', 'label', 'keyword', 'description', 'create_at',
                  'location', 'openings', 'members', 'status', 'status_display', 'contact',
                  'distance', 'is_admin', 'is_creator', 'is_default',)
        depth = 1
