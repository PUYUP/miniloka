from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from apps.person.api.validator import MsisdnNumberValidator

User = get_user_model()
VerifyCode = get_model('person', 'VerifyCode')


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
                'allow_blank': True,
                'trim_whitespace': True
            },
            'email': {
                'required': True,
                'allow_blank': True,
                'trim_whitespace': True
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._objects_model = self.Meta.model.objects


class CreateVerifyCodeSerializer(BaseVerifyCodeSerializer):
    def validate(self, data):
        # can't use both email and msisdn
        if 'email' in data and 'msisdn' in data:
            raise NotAcceptable(_("Can't use both email and msisdn"))
        return super().validate(data)

    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()

        # this logic handle if one of 'msisdn' or 'email'
        # make other not required
        # if use email, msisdn not required
        if 'email' in self.initial_data:
            kwargs['msisdn']['required'] = False
            kwargs['msisdn']['allow_blank'] = False
        
        # if use msisdn, email not required
        if 'msisdn' in self.initial_data:
            kwargs['email']['required'] = False
            kwargs['email']['allow_blank'] = False

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
        return obj


class ValidateVerifyCodeSerializer(BaseVerifyCodeSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')

        if request:
            # save verifycode token to session
            request.session['verifycode_token'] = instance.token
        
        if instance.challenge == VerifyCode.ChallengeType.PASSWORD_RECOVERY:
            ret.update({
                'password_token': self.context.get('password_token'),
                'password_uidb64': self.context.get('password_uidb64')
            })
        return ret

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        instance.validate()

        # When user loggedin and challenge is validate email or msisdn
        user = request.user
        if user.is_authenticated:
            # mark email verified
            if instance.challenge == VerifyCode.ChallengeType.VALIDATE_EMAIL:
                user.mark_email_verified()

            # mark msisdn verified
            if instance.challenge == VerifyCode.ChallengeType.VALIDATE_MSISDN:
                user.mark_msisdn_verified()

        return instance
