from django.apps import AppConfig
from django.db.models.signals import post_save

from .signals import need_save_handler, listing_member_save_handler


class ServoConfig(AppConfig):
    label = 'servo'
    name = 'apps.servo'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        Need = self.get_model('Need')
        ListingMember = self.get_model('ListingMember')

        post_save.connect(need_save_handler, sender=Need,
                          dispatch_uid='need_save_signal')

        post_save.connect(listing_member_save_handler, sender=ListingMember,
                          dispatch_uid='listing_member_signal')
