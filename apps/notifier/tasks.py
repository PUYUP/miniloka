from celery import shared_task
from .signals import notify


@shared_task
def send_notification(context):
    actor = context.pop('actor')

    notify.send(
        actor,
        **context
    )
