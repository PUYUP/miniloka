import requests
import json

from django.conf import settings

# Celery config
from celery import shared_task


@shared_task
def send_inquiry_notification(context):
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
