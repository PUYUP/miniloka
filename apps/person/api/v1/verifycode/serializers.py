from apps.person.utils.auth import get_users_by_email_or_msisdn
from apps.person.utils.generator import generate_token_uidb64_with_email, generate_token_uidb64_with_msisdn
from django.db import transaction
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable, NotFound

from utils.generals import get_model
from apps.person.api.validator import MsisdnNumberValidator

User = get_user_model()
VerifyCode = get_model('person', 'VerifyCode')

EMAIL_FIELD = settings.USER_EMAIL_FIELD
MSISDN_FIELD = settings.USER_MSISDN_FIELD


class BaseVerifyCodeSerializer(serializers.ModelSerializer):
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


class CreateVerifyCodeSerializer(BaseVerifyCodeSerializer):
    def validate(self, data):
        # can't use both email and msisdn
        if EMAIL_FIELD in data and MSISDN_FIELD in data:
            raise NotAcceptable(_("Can't use both email and msisdn"))
        return super().validate(data)

    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()

        # this logic handle if one of 'msisdn' or 'email'
        # make other not required
        # if use email, msisdn not required
        if EMAIL_FIELD in self.initial_data:
            kwargs['msisdn']['required'] = False

        # if use msisdn, email not required
        if MSISDN_FIELD in self.initial_data:
            kwargs['email']['required'] = False

        return kwargs

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

        if request:
            # save verifycode token to session
            request.session['verifycode_token'] = obj.token
        return obj


class ValidateVerifyCodeSerializer(BaseVerifyCodeSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = self.context.get('request')
        self._passcode = self.context.get('passcode')
        self._user = None

        if not self.instance:
            self._instance_query = self.instance.model.objects \
                .select_for_update()

    def validate(self, attrs):
        # Check user exists if password recovery
        if attrs.get('challenge') == VerifyCode.ChallengeType.PASSWORD_RECOVERY:
            email_or_msisdn = attrs.get('email') or attrs.get('msisdn')
            field = next((key for key, value in attrs.items()
                          if value == email_or_msisdn), None)
            active_users = get_users_by_email_or_msisdn(email_or_msisdn)
            for user in active_users:
                self._user = user
                break

            if not self._user:
                raise NotFound(
                    detail=_("User with {}: {} not found".format(field, email_or_msisdn)))
        return super().validate(attrs)

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        token = self._request.session.get('verifycode_token')

        try:
            self.instance = self._instance_query \
                .unverified_unused(**ret, token=token, passcode=self._passcode)
        except ObjectDoesNotExist:
            raise NotAcceptable(detail=_("Kode verifikasi invalid"))
        return ret

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.challenge == VerifyCode.ChallengeType.PASSWORD_RECOVERY:
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

        ret['passcode'] = instance.passcode
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
