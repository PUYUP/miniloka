import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models.expressions import Exists, OuterRef, Subquery
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from utils.validators import non_python_keyword, identifier_validator
from apps.person import settings as person_settings

VERIFICATION_FIELDS = person_settings.VERIFICATION_FIELDS


class UserManagerExtend(UserManager):
    @transaction.atomic()
    def create_user(self, username, password, **extra_fields):
        field_checker = any(
            field in VERIFICATION_FIELDS for field in extra_fields.keys())

        if not field_checker:
            raise ValueError(_("The given {} must be set".format(
                ' or '.join(VERIFICATION_FIELDS))))
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
    def roles_by_group(self):
        group_annotate = self.groups.filter(name=OuterRef('name'))
        all_groups = self.groups.model.objects.all()
        user_groups = self.groups.all()

        # generate slug for group
        # ie is_group_name
        groups_role = {
            'is_{}'.format(slugify(v.name)): Exists(Subquery(group_annotate.values('name')[:1]))
            for i, v in enumerate(user_groups)
        }

        groups = all_groups.annotate(**groups_role)
        ret = dict()

        for group in groups:
            slug = 'is_%s' % slugify(group.name)
            ret.update({slug: getattr(group, slug, False)})
        return ret

    @property
    def default_listing(self):
        try:
            return self.members.get(is_default=True).listing
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
    picture = models.ImageField(upload_to=_UPLOAD_TO, max_length=500,
                                null=True, blank=True)
    picture_original = models.ImageField(upload_to=_UPLOAD_TO, max_length=500,
                                         null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(default=Decimal(0.0), db_index=True)
    longitude = models.FloatField(default=Decimal(0.0), db_index=True)

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


class AbstractUserMeta(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='metas')

    meta_key = models.CharField(max_length=255,
                                validators=[identifier_validator, non_python_keyword])
    meta_value = models.TextField()

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _("User Meta")
        verbose_name_plural = _("User Metas")

    def __str__(self):
        return self.user.username
