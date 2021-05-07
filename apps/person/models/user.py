import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import ugettext_lazy as _

from utils.validators import non_python_keyword, identifier_validator


class UserManagerExtend(UserManager):
    @transaction.atomic()
    def create_user(self, username, password, **extra_fields):
        field_checker = any(
            field in settings.USER_VERIFICATION_FIELDS for field in extra_fields.keys())

        if not field_checker:
            raise ValueError(_("The given {} must be set".format(
                ' or '.join(settings.USER_VERIFICATION_FIELDS))))
        return super().create_user(username, password=password, **extra_fields)


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#substituting-a-custom-user-model
class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    msisdn = models.CharField(
        blank=True,
        max_length=14,
        verbose_name=_("Phone number"),
        error_messages={
            'unique': _("A user with that msisdn already exists."),
        },
    )
    email = models.EmailField(
        _('email address'),
        blank=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    is_email_verified = models.BooleanField(default=False, null=True)
    is_msisdn_verified = models.BooleanField(default=False, null=True)

    objects = UserManagerExtend()

    class Meta(AbstractUser.Meta):
        app_label = 'person'

    def clean(self, *args, **kwargs) -> None:
        return super().clean()

    @property
    def name(self):
        full_name = '{}{}'.format(self.first_name, ' ' + self.last_name)
        return full_name if self.first_name else self.username

    @property
    def is_customer(self):
        return self.groups.filter(name__in=["Customer"]).exists()

    @property
    def is_employee(self):
        return self.groups.filter(name__in=["Employee"]).exists()

    @property
    def is_owner(self):
        return self.groups.filter(name__in=["Owner"]).exists()

    @property
    def members_of(self):
        try:
            return self.members.get(is_current=True)
        except ObjectDoesNotExist:
            return None

    def mark_email_verified(self):
        self.is_email_verified = True
        self.save(update_fields=['is_email_verified'])

    def mark_msisdn_verified(self):
        self.is_msisdn_verified = True
        self.save(update_fields=['is_msisdn_verified'])


class AbstractProfile(models.Model):
    class GenderChoice(models.TextChoices):
        UNDEFINED = 'unknown', _("Unknown")
        MALE = 'male', _("Male")
        FEMALE = 'female', _("Female")

    _UPLOAD_TO = 'images/user'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='profile')

    headline = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(choices=GenderChoice.choices, blank=True, null=True,
                              default=GenderChoice.UNDEFINED, max_length=255,
                              validators=[identifier_validator, non_python_keyword])
    birthdate = models.DateField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to=_UPLOAD_TO, max_length=500,
                                null=True, blank=True)
    picture_original = models.ImageField(upload_to=_UPLOAD_TO, max_length=500,
                                         null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        return self.user.username

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name
