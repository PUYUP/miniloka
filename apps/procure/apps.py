from django.apps import AppConfig
from django.db.models.signals import post_save


class ServoConfig(AppConfig):
    label = 'procure'
    name = 'apps.procure'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        Inquiry = self.get_model('Inquiry')
        Listing = self.get_model('Listing')
        ListingMember = self.get_model('ListingMember')

        from .signals import (
            inquiry_save_handler,
            listing_member_save_handler,
            listing_save_handler
        )

        post_save.connect(inquiry_save_handler, sender=Inquiry,
                          dispatch_uid='inquiry_save_signal')

        post_save.connect(listing_save_handler, sender=Listing,
                          dispatch_uid='listing_signal')

        post_save.connect(listing_member_save_handler, sender=ListingMember,
                          dispatch_uid='listing_member_signal')
