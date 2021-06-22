import phonenumbers

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from utils.generals import get_model

UserModel = get_user_model()
SecureCode = get_model('person', 'SecureCode')


# Password verification
class PasswordValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        validate_password(value)


# Check duplicate email if has verified
class EmailDuplicateValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        user = UserModel.objects.filter(email=value, is_email_verified=True)
        if user.exists():
            raise serializers.ValidationError(
                _("Email {email} sudah terdaftar.".format(email=value))
            )


# Check duplicate msisdn if has verified
class MsisdnDuplicateValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        user = UserModel.objects.filter(msisdn=value, is_msisdn_verified=True)
        if user.exists():
            raise serializers.ValidationError(
                _("Nomor telepon {msisdn} sudah terdaftar".format(msisdn=value)))


# Check duplicate msisdn if has verified
class MsisdnNumberValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        if not value.isnumeric() or not value:
            raise serializers.ValidationError(
                _("Nomor telepon hanya boleh angka"))

        try:
            phone = phonenumbers.parse(value, 'ID')
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError(_("Invalid format"))
        except:
            raise serializers.ValidationError(_("Not msisdn"))
