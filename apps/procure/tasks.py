import requests
import json

from django.contrib.auth import get_user_model
from django.conf import settings

# Celery config
from celery import shared_task

from apps.notifier.signals import notify
from utils.generals import get_model

UserModel = get_user_model()
Listing = get_model('procure', 'Listing')
Inquiry = get_model('procure', 'Inquiry')
Offer = get_model('procure', 'Offer')
Order = get_model('procure', 'Order')


@shared_task
def send_fcm_notification(**context):
    url = 'https://fcm.googleapis.com/fcm/send'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key=' + settings.FCM_SERVER_KEY
    }
    data = {
        'registration_ids': context.get('fcm_tokens'),
        'notification': {
            'title': '{} {}'.format(context.get('inquiry_user'), 'mengirim permintaan'),
            'body': context.get('inquiry_keyword')
        }
    }

    requests.post(url, headers=headers, data=json.dumps(data))


@shared_task
def send_inquiry_notification(**context):
    print(context, 'XXXXXXXXXXXXX')
    actor = context.pop('actor')
    recipient = context.pop('recipient')
    action_object = context.pop('action_object')
    target = context.pop('target')

    actor_obj = UserModel.objects.get(id=actor)
    recipient_obj = UserModel.objects.filter(id__in=recipient)
    action_object_obj = Inquiry.objects.get(id=action_object)
    target_obj = Listing.objects.filter(id__in=target)

    notify.send(
        actor_obj,
        recipient=recipient_obj,
        action_object=action_object_obj,
        target=target_obj,
        **context
    )


@shared_task
def send_offer_notification(**context):
    actor = context.pop('actor')
    recipient = context.pop('recipient')
    action_object = context.pop('action_object')
    target = context.pop('target')

    actor_obj = UserModel.objects.get(id=actor)
    recipient_obj = UserModel.objects.get(id=recipient)
    action_object_obj = Offer.objects.get(id=action_object)
    target_obj = Inquiry.objects.get(id=target)

    notify.send(
        actor_obj,
        recipient=recipient_obj,
        action_object=action_object_obj,
        target=target_obj,
        **context
    )


@shared_task
def send_order_notification(**context):
    actor = context.pop('actor')
    recipient = context.pop('recipient')
    action_object = context.pop('action_object')
    target = context.pop('target')

    actor_obj = UserModel.objects.get(id=actor)
    recipient_obj = UserModel.objects.get(id=recipient)
    action_object_obj = Order.objects.get(id=action_object)
    target_obj = Offer.objects.get(id=target)

    notify.send(
        actor_obj,
        recipient=recipient_obj,
        action_object=action_object_obj,
        target=target_obj,
        **context
    )
