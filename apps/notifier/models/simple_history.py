import uuid

from django.db import models
from simple_history import register
from utils.generals import get_model

Notification = get_model('notifier', 'Notification')


register(Notification, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))
