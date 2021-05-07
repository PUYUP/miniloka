from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from utils.generals import get_model

OfferRate = get_model('servo', 'OfferRate')


class OfferRateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = OfferRate
        fields = ('cost', 'description', 'create_at', 'user',
                  'can_goto', 'can_goto_radius', 'is_newest',
                  'latitude', 'longitude',)
