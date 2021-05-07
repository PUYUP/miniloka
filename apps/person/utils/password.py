from utils.generals import get_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()


class PasswordRecovery:
    """
    :obtain verify send to? (email or msisdn)

    :token and :uidb64 generated with user credential
    """

    def __init__(self, new_password, retype_password, token, uidb64):
        self.new_password = str(new_password)
        self.retype_password = str(retype_password)
        self.token = token
        self.uidb64 = uidb64
        self.verifycode = None

    def _validate_password(self):
        if self.new_password != self.retype_password:
            raise ValidationError(message=_("Password tidak sama"),
                                  code='password_not_match')

        try:
            validate_password(self.retype_password)
        except ValidationError as e:
            raise ValidationError(message=' '.join(e.messages),
                                  code='password_invalid')

    def _validate_token(self):
        user = self._get_user()
        isvalid = default_token_generator.check_token(user, self.token)
        if not isvalid:
            raise ValidationError(message=_("Token invalid"))

    def _get_user(self):
        uid = urlsafe_base64_decode(self.uidb64).decode()

        try:
            user = UserModel._default_manager.get(pk=uid)
        except ObjectDoesNotExist:
            raise ValidationError(message=_("Invalid user"),
                                  code='user_not_found')
        return user

    def get_verifycode(self, token, field, value, passcode):
        VerifyCode = get_model('person', 'VerifyCode')
        obtain = {field: value}
        challenge = 'password_recovery'

        try:
            self.verifycode = VerifyCode.objects.select_for_update() \
                .verified_unused(token=token, challenge=challenge,
                                 passcode=passcode, **obtain)
        except ObjectDoesNotExist:
            return ValidationError(message=_("Invalid verify code"),
                                   code='verifycode_invalid')

    def save_password(self):
        if self.verifycode is None:
            raise ValidationError(message=_("Empty verify code"),
                                  code='verifycode_empty')

        self._validate_password()
        self._validate_token()

        user = self._get_user()
        self.verifycode.mark_used()
        user.set_password(self.retype_password)
        user.save()


class ChangePassword:
    def __init__(self, user, old_password, new_password, retype_password):
        self.user = user
        self.old_password = old_password
        self.new_password = new_password
        self.retype_password = retype_password

    def _validate_old_password(self):
        if not self.user.check_password(self.old_password):
            raise ValidationError(message=_("Password lama salah"),
                                  code='wrong_old_password')

    def _validate_password(self):
        if self.new_password != self.retype_password:
            raise ValidationError(message=_("Password tidak sama"),
                                  code='password_not_match')

        try:
            validate_password(self.retype_password)
        except ValidationError as e:
            raise ValidationError(message=' '.join(e.messages),
                                  code='password_invalid')

    def save_password(self):
        self._validate_old_password()
        self._validate_password()

        self.user.set_password(self.retype_password)
        self.user.save()
