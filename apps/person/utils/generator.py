from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from apps.person.utils.auth import get_users_by

UserModel = get_user_model()


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


def generate_username(full_name):
    name = full_name.split(' ')
    username = slugify(name[0])

    if UserModel.objects.filter(username=username).count() > 0:
        users = UserModel.objects \
            .filter(username__regex=r'^%s[1-9]{1,}$' % username) \
            .order_by('username') \
            .values('username')

        if len(users) > 0:
            last_number_used = map(lambda x: int(
                x['username'].replace(username, '')), users)
            last_number_used.sort()
            last_number_used = last_number_used[-1]
            number = last_number_used + 1
            username = '%s%s' % (username, number)
        else:
            username = '%s%s' % (username, 1)

        return username
    return slugify(username)
