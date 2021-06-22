from .user import *
from .securecode import *

from django.contrib.auth.models import Group
from utils.generals import is_model_registered

__all__ = list()

# Add custom field to group
Group.add_to_class('is_default', models.BooleanField(default=False))


# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#auth-custom-user
if not is_model_registered('person', 'User'):
    class User(User):
        class Meta(User.Meta):
            pass

    __all__.append('User')


# 1
if not is_model_registered('person', 'Profile'):
    class Profile(AbstractProfile):
        class Meta(AbstractProfile.Meta):
            pass

    __all__.append('Profile')


# 2
if not is_model_registered('person', 'SecureCode'):
    class SecureCode(AbstractSecureCode):
        class Meta(AbstractSecureCode.Meta):
            pass

    __all__.append('SecureCode')


# 3
if not is_model_registered('person', 'UserMeta'):
    class UserMeta(AbstractUserMeta):
        class Meta(AbstractUserMeta.Meta):
            pass

    __all__.append('UserMeta')
