from django.apps import AppConfig
from django.db.models.signals import post_save


class PersonConfig(AppConfig):
    label = 'person'
    name = 'apps.person'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from django.conf import settings
        from django.contrib.auth.models import Group
        from .signals import (
            user_save_handler,
            group_save_handler,
            securecode_save_handler
        )

        SecureCode = self.get_model('SecureCode')

        # User
        post_save.connect(user_save_handler, sender=settings.AUTH_USER_MODEL,
                          dispatch_uid='user_save_signal')

        # Secure code
        post_save.connect(securecode_save_handler, sender=SecureCode,
                          dispatch_uid='securecode_save_signal')

        # Group
        post_save.connect(group_save_handler, sender=Group,
                          dispatch_uid='group_save_signal')
