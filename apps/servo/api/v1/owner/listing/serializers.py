from django.db import transaction
from rest_framework import serializers
from utils.generals import get_model

Listing = get_model('servo', 'Listing')
ListingMember = get_model('servo', 'ListingMember')
ListingLocation = get_model('servo', 'ListingLocation')


class ListingLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingLocation
        fields = '__all__'
        depth = 1


class BaseListingSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='servo_api:owner:listing-detail',
                                               lookup_field='uuid', read_only=True)
    location = ListingLocationSerializer()
    status_display = serializers.SerializerMethodField()

    def get_status_display(self, instance):
        return instance.get_status_display()


class CreateListingSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Listing
        fields = ('user', 'label', 'description',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context.get('request')
        self._user = None

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        self._user = data.pop('user', None)  \
            or self.initial_data.pop('user', None)

        # don't allow user set 'status' directly
        _status = data.pop('status', None) \
            or self.initial_data.pop('status', None)
        return data

    @transaction.atomic()
    def create(self, validated_data):
        instance, created = Listing.objects \
            .filter(members__user_id=self._user.id) \
            .get_or_create(**validated_data)

        if instance and created:
            ListingMember.objects \
                .create(user_id=self._user.id, listing_id=instance.id,
                        is_creator=True, is_allow_offer=True)
        return instance


class ListListingSerializer(BaseListingSerializer):
    class Meta:
        model = Listing
        fields = ('uuid', 'label', 'description', 'create_at',
                  'location', 'status', 'status_display',)


class RetrieveListingSerializer(BaseListingSerializer):
    class Meta:
        model = Listing
        fields = ('uuid', 'label', 'description', 'create_at',
                  'location', 'status', 'status_display',)
