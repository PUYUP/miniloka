from rest_framework import serializers

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


class ListListingProductSerializer(BaseListingProductSerializer):
    class Meta(BaseListingProductSerializer.Meta):
        fields = ('uuid', 'label', 'description',)


class RetrieveListingProductSerializer(BaseListingProductSerializer):
    class Meta(BaseListingProductSerializer.Meta):
        fields = '__all__'
        depth = 1
