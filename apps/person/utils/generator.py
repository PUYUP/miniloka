from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from apps.person.utils.auth import get_users_by


def _generate_token_uidb64(active_users):
    token = None
    uidb64 = None
    for user in active_users:
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        break
    return token, uidb64


def generate_token_uidb64_with_email(email):
    """Return token and uidb64"""
    active_users = get_users_by(value=email)
    return _generate_token_uidb64(active_users)


def generate_token_uidb64_with_msisdn(msisdn):
    """Return token and uidb64"""
    active_users = get_users_by(field='msisdn', value=msisdn)
    return _generate_token_uidb64(active_users)
