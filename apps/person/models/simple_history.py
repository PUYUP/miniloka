import uuid

from django.db import models
from django.contrib.auth import get_user_model

from simple_history import register
from utils.generals import get_model

UserModel = get_user_model()
Profile = get_model('person', 'Profile')
SecureCode = get_model('person', 'SecureCode')

register(UserModel, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Profile, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(SecureCode, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))
