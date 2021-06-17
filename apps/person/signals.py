from django.db import transaction, IntegrityError
from django.db.models import Q
from django.contrib.auth.models import Group
from utils.generals import get_model

from .tasks import send_verifycode_email, send_verifycode_msisdn

Profile = get_model('person', 'Profile')


@transaction.atomic
def user_save_handler(sender, instance, created, **kwargs):
    if created:
        profile = getattr(instance, 'profile', None)
        if profile is None:
            try:
                Profile.objects.create(user=instance)
            except IntegrityError:
                pass

    if not created:
        # create Profile if not exist
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)


@transaction.atomic
def group_save_handler(sender, instance, created, **kwargs):
    is_default = getattr(instance, 'is_default')
    if is_default:
        groups = Group.objects.exclude(id=instance.id)
        if groups.exists():
            groups.update(is_default=False)


@transaction.atomic
def verifycode_save_handler(sender, instance, created, **kwargs):
    # create tasks
    # run only on resend and created
    if instance.is_used == False and instance.is_verified == False:
        data = {'passcode': getattr(instance, 'passcode', None)}

        # Send via email
        if instance.email:
            data.update({'email': getattr(instance, 'email', None)})
            send_verifycode_email.delay(data)  # with celery
            # send_verifycode_email(data)  # without celery

        # Send via SMS
        if instance.msisdn:
            data.update({'msisdn': getattr(instance, 'msisdn', None)})
            send_verifycode_msisdn.delay(data)  # with celery
            # send_verifycode_msisdn(data)  # without celery

        # mark oldest VerifyCode as expired
        obtain = instance.msisdn or instance.email
        cls = instance.__class__
        oldest = cls.objects \
            .filter(
                Q(challenge=instance.challenge),
                Q(email=obtain) | Q(msisdn=obtain),
                Q(is_used=False), Q(is_expired=False)
            ).exclude(passcode=instance.passcode)

        if oldest.exists():
            oldest.update(is_expired=True)
