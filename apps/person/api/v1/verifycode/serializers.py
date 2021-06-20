from django.db import transaction
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable, NotFound

from utils.generals import get_model
from utils.mixin.api import ExcludeFieldsModelSerializer
from apps.person.api.validator import MsisdnNumberValidator
from apps.person.utils.auth import get_users_by_email_or_msisdn
from apps.person.utils.generator import generate_token_uidb64_with_email, generate_token_uidb64_with_msisdn

User = get_user_model()
VerifyCode = get_model('person', 'VerifyCode')

EMAIL_FIELD = settings.USER_EMAIL_FIELD
MSISDN_FIELD = settings.USER_MSISDN_FIELD


class BaseVerifyCodeSerializer(ExcludeFieldsModelSerializer):
    class Meta:
        model = VerifyCode
        fields = ('uuid', 'email', 'msisdn', 'challenge',
                  'valid_until', 'is_verified',)
        read_only_fields = ('uuid', 'is_verified',)
        extra_kwargs = {
            'challenge': {
                'required': True
            },
            'msisdn': {
                'required': True,
                'min_length': 8,
                'max_length': 15,
                'validators': [MsisdnNumberValidator()],
                'allow_blank': False,
                'trim_whitespace': True
            },
            'email': {
                'required': True,
                'allow_blank': False,
                'trim_whitespace': True
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._objects_model = self.Meta.model.objects
        self._request = self.context.get('request')
        self._user = None
        self._password_recovery = VerifyCode.ChallengeType.PASSWORD_RECOVERY.value

    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()
        data = self._kwargs.get('data')

        # this logic handle if one of 'msisdn' or 'email'
        # make other not required
        # if use email, msisdn not required
        if data:
            if EMAIL_FIELD in data:
                kwargs['msisdn']['required'] = False

            # if use msisdn, email not required
            if MSISDN_FIELD in data:
                kwargs['email']['required'] = False

        return kwargs


class CreateVerifyCodeSerializer(BaseVerifyCodeSerializer):
    class Meta(BaseVerifyCodeSerializer.Meta):
        model = VerifyCode
        fields = ('email', 'msisdn', 'challenge',)

    def validate(self, attrs):
        # can't use both email and msisdn
        if EMAIL_FIELD in attrs and MSISDN_FIELD in attrs:
            raise NotAcceptable(_("Can't use both email and msisdn"))

        # Check user exists
        challenge = attrs.get('challenge')
        email_validation = VerifyCode.ChallengeType.EMAIL_VALIDATION.value
        msisdn_validation = VerifyCode.ChallengeType.MSISDN_VALIDATION.value

        change_email = VerifyCode.ChallengeType.CHANGE_EMAIL.value
        change_msisdn = VerifyCode.ChallengeType.CHANGE_MSISDN.value

        if challenge in {self._password_recovery, email_validation, msisdn_validation, change_email, change_msisdn}:
            email_or_msisdn = attrs.get('email') or attrs.get('msisdn')
            field = next((key for key, value in attrs.items()
                          if value == email_or_msisdn), None)
            active_users = get_users_by_email_or_msisdn(email_or_msisdn)
            for user in active_users:
                self._user = user
                break

            # if password recovery check email/msisdn must exists in database
            if challenge == self._password_recovery:
                if not self._user:
                    error = _("User with {}: {} not found".format(
                        field, email_or_msisdn))
                    raise NotFound(detail=error)

            # if register action check email/msisdn not exists in database
            if challenge in {email_validation, msisdn_validation, change_email, change_msisdn}:
                if self._user:
                    error = _("{}: {} has registered".format(
                        field.capitalize(), email_or_msisdn))
                    raise NotAcceptable(detail=error)

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request', None)
        user_agent = request.META['HTTP_USER_AGENT']

        validated_data.update({
            'user_agent': user_agent,
            'is_verified': False,
            'is_used': False,
            'is_expired': False
        })

        # If `valid_until` greater than time now we update VerifyCode Code
        obj, _created = self._objects_model.generate(data={**validated_data})
        return obj


class ValidateVerifyCodeSerializer(BaseVerifyCodeSerializer):
    class Meta(BaseVerifyCodeSerializer.Meta):
        model = VerifyCode
        fields = ('email', 'msisdn', 'challenge', 'token',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._passcode = self.context.get('passcode')

        if not self.instance:
            self._instance_query = self.instance.model.objects \
                .select_for_update()

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        try:
            self.instance = self._instance_query \
                .unverified_unused(**ret, passcode=self._passcode)
        except ObjectDoesNotExist:
            raise NotAcceptable(detail=_("Kode verifikasi invalid"))
        return ret

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        instance.validate()

        # When user loggedin and challenge is validate email or msisdn
        user = request.user
        if user.is_authenticated:
            # mark email verified
            if instance.challenge == VerifyCode.ChallengeType.EMAIL_VALIDATION:
                user.mark_email_verified()

            # mark msisdn verified
            if instance.challenge == VerifyCode.ChallengeType.MSISDN_VALIDATION:
                user.mark_msisdn_verified()

        return instance


class RetrieveVerifyCodeSerialzer(BaseVerifyCodeSerializer):
    class Meta(BaseVerifyCodeSerializer.Meta):
        model = VerifyCode
        fields = ('challenge', 'email', 'msisdn', 'is_verified', 'token',)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # show this after verified
        if instance.is_verified:
            # return value if password recovery
            if instance.challenge == self._password_recovery:
                password_token = None
                password_uidb64 = None
                email = getattr(instance, 'email')
                msisdn = getattr(instance, 'msisdn')

                if email:
                    password_token, password_uidb64 = generate_token_uidb64_with_email(
                        instance.email)

                if msisdn:
                    password_token, password_uidb64 = generate_token_uidb64_with_msisdn(
                        instance.msisdn)

                if password_token and password_uidb64:
                    ret.update({
                        'password_token': password_token,
                        'password_uidb64': password_uidb64
                    })

            ret.update({'passcode': instance.passcode})
        return ret
