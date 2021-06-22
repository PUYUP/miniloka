from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.core.validators import EmailValidator
from django.contrib.auth.models import Group
from django.urls import reverse

from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError

from utils.generals import get_model
from apps.person.api.validator import (
    EmailDuplicateValidator,
    MsisdnDuplicateValidator,
    MsisdnNumberValidator
)

from ..profile.serializers import ProfileSerializer

UserModel = get_user_model()
User = get_model('person', 'User')
UserMeta = get_model('person', 'UserMeta')
SecureCode = get_model('person', 'SecureCode')

EMAIL_FIELD = settings.USER_MSISDN_FIELD
MSISDN_FIELD = settings.USER_EMAIL_FIELD


class CustomExcpetion(PermissionDenied):
    default_code = 'invalid'

    def __init__(self, detail, status_code=None):
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code


class DynamicFields(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        context = kwargs.get('context', dict())
        request = context.get('request', None)

        # Instantiate the superclass normally
        super(DynamicFields, self).__init__(*args, **kwargs)

        # Allow only this field on update
        if request.method == 'PATCH':
            # Only this fields allowed update
            fields = ('username', 'first_name', 'email', 'msisdn',)

        if fields is not None and fields != '__all__':
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class BaseUserSerializer(DynamicFields, serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True)
    profile = ProfileSerializer(many=False, read_only=True)

    # email and msisdn inquiry verification
    # example: {"passcode": "123456", "token": "1ufufa", "challenge": "email_validation"}
    verification = serializers.JSONField(write_only=True, required=True)

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 6
            },
            'first_name': {
                'required': True
            },
            'username': {
                'required': True,
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'required': True,
                'validators': [EmailValidator(), EmailDuplicateValidator()]
            },
            'msisdn': {
                'required': True,
                'validators': [MsisdnNumberValidator(), MsisdnDuplicateValidator()],
                'min_length': 8,
                'max_length': 14
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove verification process
        if not settings.USER_REQUIRED_VERIFICATION:
            self.fields.pop('verification', None)

        self._request = self.context.get('request')
        self._securecode_instance = None
        self._verify_field = None
        self._verify_value = None

    def get_links(self, instance):
        return {
            'retrieve': self._request.build_absolute_uri(
                reverse('person_api:user-detail',
                        kwargs={'uuid': instance.uuid})
            ),
            'metas': self._request.build_absolute_uri(
                reverse('person_api:user-meta',
                        kwargs={'uuid': instance.uuid})
            ),
        }

    def _run_verification(self, verification):
        """ Before account created validate email or msisdn """
        verify_field_value = {self._verify_field: self._verify_value}

        try:
            self._securecode_instance = SecureCode.objects.select_for_update() \
                .verified_unused(**verification, **verify_field_value)
        except ObjectDoesNotExist:
            raise CustomExcpetion({'verification': _("{} belum diverifikasi".format(self._verify_field.upper()))},
                                  status_code=status.HTTP_401_UNAUTHORIZED)

    def _mark_securecode_used(self, instance):
        if self._securecode_instance:
            self._securecode_instance.mark_used()

            # mark field verified
            field_model = 'is_{}_verified'.format(self._verify_field)

            setattr(instance, field_model, True)
            instance.save(update_fields=[field_model])

    def validate(self, attrs):
        self._verify_value = attrs.get('email') or attrs.get('msisdn')
        self._verify_field = next((key for key, value in attrs.items()
                                   if value == self._verify_value), None)

        # verification required!
        if (self._verify_field and self._verify_value) \
                and settings.USER_REQUIRED_VERIFICATION:
            verification = attrs.pop('verification', {}) \
                or self.initial_data.pop('verification', {})

            self._run_verification(verification)
        return super().validate(attrs)


class CreateUserSerializer(BaseUserSerializer):
    # Added some requirement for register
    retype_password = serializers.CharField(max_length=255, write_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = ('username', 'first_name', 'email', 'msisdn',
                  'password', 'retype_password', 'verification',)

    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()

        # If one of email or msisdn exists
        if EMAIL_FIELD in self.initial_data:
            kwargs[MSISDN_FIELD]['required'] = False

        elif MSISDN_FIELD in self.initial_data:
            kwargs[EMAIL_FIELD]['required'] = False

        # mark username not-required if first_name exist
        if 'first_name' in self.initial_data:
            kwargs['username']['required'] = False

        # mark first_name not-required if username exist
        if 'username' in self.initial_data:
            kwargs['first_name']['required'] = False

        return kwargs

    def validate(self, data):
        # can't use both email and msisdn
        if EMAIL_FIELD in data and MSISDN_FIELD in data:
            raise ValidationError(
                {'field_error': _("Can't use both email and msisdn")})

        # confirm password
        password = data.get('password')
        retype_password = data.pop('retype_password')
        if password != retype_password:
            raise ValidationError({
                'retype_password': _("Password tidak sama")
            })

        return super().validate(data)

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.get('username')
        first_name = validated_data.get('first_name')

        # generate first name from username
        if 'first_name' not in validated_data:
            validated_data.update({'first_name': username})

        # generate username if not define
        if 'username' not in validated_data:
            now = datetime.now()
            trim_first_name = first_name[:4]
            timestamp_only = str(datetime.timestamp(now)).split('.', 1)[0]
            new_username = '{}-{}'.format(trim_first_name, timestamp_only)
            validated_data.update({'username': slugify(new_username)})

        # set user is_active to True
        validated_data.update({'is_active': True})

        try:
            instance = UserModel.objects.create_user(**validated_data)
        except (IntegrityError, TypeError, ValueError) as e:
            raise DjangoValidationError(str(e))

        # set default group
        try:
            group = Group.objects.get(is_default=True)
            group.user_set.add(instance)
        except ObjectDoesNotExist:
            pass

        # mark securecode as used
        self._mark_securecode_used(instance)
        return instance


class UpdateUserSerializer(BaseUserSerializer):
    @transaction.atomic
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if hasattr(instance, key):
                if key == 'password':
                    instance.set_password(value)
                else:
                    old_value = getattr(instance, key, None)
                    if old_value != value:
                        setattr(instance, key, value)
        instance.save()

        # mark securecode as used
        self._mark_securecode_used(instance)
        return instance


class RetrieveUserSerializer(BaseUserSerializer):
    links = None

    class Meta(BaseUserSerializer.Meta):
        fields = ('uuid', 'email', 'msisdn', 'first_name', 'username', 'name',
                  'profile', 'is_email_verified', 'is_msisdn_verified')
        depth = 1


class UserMetaSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserMeta
        fields = ['user', 'meta_key', 'meta_value', ]

    @transaction.atomic()
    def create(self, validated_data):
        defaults = {
            'meta_value': validated_data.pop('meta_value')
        }

        instance, _created = UserMeta.objects \
            .update_or_create(defaults=defaults, **validated_data)
        return instance
