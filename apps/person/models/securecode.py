import uuid
import pyotp

from django.db import models, transaction
from django.db.models import Q, Case, When, Value
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator, ValidationError
from django.utils import timezone
from utils.validators import non_python_keyword


class SecureCodeQuerySet(models.query.QuerySet):
    def _base_query(self, email=None, msisdn=None, token=None,
                    passcode=None, challenge=None):
        qs = self.filter(Q(email=Case(When(email__isnull=False, then=Value(email))))
                         | Q(msisdn=Case(When(msisdn__isnull=False, then=Value(msisdn)))),
                         Q(is_expired=False),
                         Q(challenge=challenge),
                         Q(token=token),
                         Q(passcode=passcode))
        return qs

    def verified_unused(self, email=None, msisdn=None, token=None,
                        challenge=None, passcode=None):
        qs = self._base_query(
            email,
            msisdn,
            token,
            passcode,
            challenge
        ).get(is_verified=True, is_used=False)

        return qs

    def unverified_unused(self, email=None, msisdn=None, token=None,
                          challenge=None, passcode=None):
        qs = self._base_query(
            email,
            msisdn,
            token,
            passcode,
            challenge
        ).get(is_verified=False, is_used=False)

        return qs

    def generate(self, *args, **kwargs):
        """Generate if valid_until greather than now"""
        data = kwargs.get('data', {})
        obj, created = self.filter(valid_until__gt=timezone.now()) \
            .update_or_create(**data, defaults=data)
        return obj, created


class AbstractSecureCode(models.Model):
    class ChallengeType(models.TextChoices):
        EMAIL_VALIDATION = 'email_validation', _("Validate Email")
        MSISDN_VALIDATION = 'msisdn_validation', _("Validate MSISDN")
        PASSWORD_RECOVERY = 'password_recovery', _("Password Recovery")
        USERNAME_RECOVERY = 'username_recovery', _("Username Recovery")
        CHANGE_MSISDN = 'change_msisdn', _("Change MSISDN")
        CHANGE_EMAIL = 'change_email', _("Change Email")
        CHANGE_USERNAME = 'change_username', _("Change Username")
        CHANGE_PASSWORD = 'change_password', _("Change Password")

    """
    Send SecureCode Code with;
        :email
        :msisdn (SMS or Voice Call)

    :valid_until; SecureCode Code validity max date (default 2 hour)
    :is_expired; expired
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    email = models.EmailField(null=True, blank=True)
    msisdn = models.CharField(null=True, blank=True, max_length=14)

    # part by system
    token = models.CharField(max_length=64)
    passcode = models.CharField(max_length=25)
    challenge = models.SlugField(
        choices=ChallengeType.choices,
        max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
            non_python_keyword
        ]
    )
    valid_until = models.DateTimeField(blank=True, null=True, editable=False)
    valid_until_timestamp = models.IntegerField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    user_agent = models.TextField(null=True, blank=True)

    objects = SecureCodeQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _("Secure Code")
        verbose_name_plural = _("Secure Codes")

    def __str__(self):
        return self.passcode

    def validate(self):
        if self.is_used:
            raise ValidationError(
                {'is_used': _("Has used on %s" % (self.update_at))})

        if self.is_verified:
            raise ValidationError(
                {'is_verified': _("Has verified on %s" % (self.update_at))})

        if self.is_expired:
            raise ValidationError(
                {'is_expired': _("Has expired on %s" % (self.update_at))})

        if timezone.now() >= self.valid_until:
            self.is_expired = True
            self.save(update_fields=['is_expired'])
            raise ValidationError(
                {'valid_until': _("SecureCode code expired on %s" % (self.valid_until))})

        # now real validation
        tsecurecode = pyotp.TOTP(self.token)
        passed = tsecurecode.verify(
            self.passcode, for_time=self.valid_until_timestamp)
        if not passed:
            raise ValidationError({'passcode': _("SecureCode Code invalid")})

        # all passed and mark as verified!
        self.is_verified = True
        self.save(update_fields=['is_verified'])

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])

    def generate_passcode(self):
        # Set max validity date
        # Default 2 hours since created
        self.valid_until = timezone.now() + timezone.timedelta(hours=2)
        self.valid_until_timestamp = self.valid_until.replace(
            microsecond=0).timestamp()

        # generate SecureCode
        token = pyotp.random_base32()
        totp = pyotp.TOTP(token)
        passcode = totp.at(self.valid_until_timestamp)

        # save to database
        self.passcode = passcode
        self.token = token

    @transaction.atomic()
    def save(self, *args, **kwargs):
        # generate SecureCode code
        if not self.is_verified:
            self.generate_passcode()
        super().save(*args, **kwargs)
