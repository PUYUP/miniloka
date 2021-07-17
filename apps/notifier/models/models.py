from .notification import *

from utils.generals import is_model_registered

__all__ = list()


# 1
if not is_model_registered('notifier', 'Notification'):
    class Notification(AbstractNotification):
        class Meta(AbstractNotification.Meta):
            pass

    __all__.append('Notification')
