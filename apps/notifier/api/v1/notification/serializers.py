from django.urls import reverse

from rest_framework import serializers

from utils.generals import get_model

Notification = get_model('notifier', 'Notification')


class NotificationSerializer(serializers.ModelSerializer):
    display_verb = serializers.CharField(read_only=True)
    links = serializers.SerializerMethodField()
    action_object_uuid = serializers.UUIDField(read_only=True)
    target_uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self._context.get('request')

    def get_links(self, instance):
        ret = {
            'mark_read': self._request.build_absolute_uri(
                reverse('notifier_api:notification-mark_read',
                        kwargs={'uuid': instance.uuid})
            ),
            'mark_unread': self._request.build_absolute_uri(
                reverse('notifier_api:notification-mark_unread',
                        kwargs={'uuid': instance.uuid})
            ),
        }

        return ret
