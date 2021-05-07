from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.core.validators import EmailValidator
from django.contrib.auth.models import Group

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
VerifyCode = get_model('person', 'VerifyCode')

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
    url = serializers.HyperlinkedIdentityField(view_name='person_api:user-detail',
                                               lookup_field='uuid', read_only=True)
    name = serializers.CharField(read_only=True)
    profile = ProfileSerializer(many=False, read_only=True)

    # email and msisdn need verification
    # format: {"passcode": "123456", "challenge": "email_validation"}
    verification = serializers.DictField(write_only=True, required=True,
                                         child=serializers.CharField())

    class Meta:
        model = User
        exclude = ('id', 'user_permissions', 'date_joined',
                   'is_superuser', 'last_login', 'is_staff',)
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

        self._verifycode_obj = None
        self._verify_field = None
        self._verify_value = None

    def _run_verification(self, verification):
        """
        Before register user must validate
        email or msisdn
        this function will check that
        """

        request = self.context.get('request')
        verify_field_value = {self._verify_field: self._verify_value}
        token = request.session.get('verifycode_token') if request else None

        try:
            self._verifycode_obj = VerifyCode.objects.select_for_update() \
                .verified_unused(token=token, **verification, **verify_field_value)
        except ObjectDoesNotExist:
            raise CustomExcpetion({'verification': _("{} belum diverifikasi".format(self._verify_field.upper()))},
                                  status_code=status.HTTP_401_UNAUTHORIZED)

    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()

        # If one of email or msisdn exists
        # make other not required
        if hasattr(self, 'initial_data'):
            if EMAIL_FIELD in self.initial_data:
                kwargs[MSISDN_FIELD]['required'] = False
            elif MSISDN_FIELD in self.initial_data:
                kwargs[EMAIL_FIELD]['required'] = False
        return kwargs

    def validate(self, attrs):
        self._verify_value = attrs.get('email') or attrs.get('msisdn')
        self._verify_field = next((key for key, value in attrs.items()
                                   if value == self._verify_value), None)

        verification = attrs.pop('verification', {}) \
            or self.initial_data.pop('verification', {})

        if (self._verify_field and self._verify_value) \
                and settings.USER_REQUIRED_VERIFICATION:
            self._run_verification(verification)
        return super().validate(attrs)


class CreateUserSerializer(BaseUserSerializer):
    # Added some requirement for register
    retype_password = serializers.CharField(max_length=255, write_only=True)
    groups = serializers.SlugRelatedField(slug_field='name', write_only=True,
                                          required=False, queryset=Group.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._groups = None
        self._groups_instance = None

    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()

        # mark username not-required if first_name exist
        if 'first_name' in self.initial_data:
            kwargs['username']['required'] = False

        # mark first_name not-required if username exist
        if 'username' in self.initial_data:
            kwargs['first_name']['required'] = False

        return kwargs

    def to_internal_value(self, data):
        # use username as first_name
        if 'first_name' not in data:
            data['first_name'] = data.get('username')

        # create username
        if 'username' not in data:
            # current date and time
            now = datetime.now()
            xchar = data['first_name'][:4]
            xtime = str(datetime.timestamp(now)).split('.', 1)[0]
            username = slugify('{}-{}'.format(xchar, xtime))
            data['username'] = username

        # get groups
        self._groups = data.pop('groups', None)  \
            or self.initial_data.pop('groups', None)
        return super().to_internal_value(data)

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

        # get groups instance
        # if not exists use default groups
        q_groups = Q()
        if self._groups:
            q_groups = Q(name=self._groups)
        else:
            q_groups = Q(is_default=True)

        try:
            self._groups_instance = Group.objects.get(q_groups)
        except ObjectDoesNotExist:
            pass

        return super().validate(data)

    @transaction.atomic
    def create(self, validated_data):
        try:
            instance = UserModel.objects.create_user(**validated_data)
        except (IntegrityError, TypeError, ValueError) as e:
            raise DjangoValidationError(str(e))

        if self._groups_instance:
            self._groups_instance.user_set.add(instance)

        # mark verifycode as used
        if self._verifycode_obj:
            self._verifycode_obj.mark_used()

            # mark field used in otp verified
            field_model = 'is_{}_verified'.format(self._verify_field)

            setattr(instance, field_model, True)
            instance.save(update_fields=[field_model])
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

        # mark verifycode as used
        if self._verifycode_obj:
            self._verifycode_obj.mark_used()
        return instance


class RetrieveUserSerializer(DynamicFields, serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = User
        fields = '__all__'
        depth = 1
