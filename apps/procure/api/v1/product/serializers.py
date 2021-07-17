from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from utils.generals import get_model

Listing = get_model('procure', 'Listing')
ListingProduct = get_model('procure', 'ListingProduct')


class BaseListingProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingProduct


class CreateListingProductSerializer(BaseListingProductSerializer):
    listing = serializers.SlugRelatedField(slug_field='uuid',
                                           queryset=Listing.objects.all())

    class Meta(BaseListingProductSerializer.Meta):
        fields = ('listing', 'label', 'description',)

    def validate(self, attrs):
        request = self.context.get('request')
        data = super().validate(attrs)
        listing = data.get('listing')

        # only admin can submit product
        listing_members = listing.members \
            .filter(user_id=request.user.id, is_admin=True)

        if not listing_members.exists():
            raise serializers.ValidationError(
                detail=_("Bukan bagian dari bisnis ini")
            )
        return data


class ListListingProductSerializer(BaseListingProductSerializer):
    class Meta(BaseListingProductSerializer.Meta):
        fields = ('uuid', 'label', 'description',)


class RetrieveListingProductSerializer(BaseListingProductSerializer):
    class Meta(BaseListingProductSerializer.Meta):
        fields = '__all__'
        depth = 1
