from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

UserModel = get_user_model()


class UserChangeFormExtend(UserChangeForm):
    """ Override user Edit form """

    def clean_email(self):
        email = self.cleaned_data.get('email', None)

        # Make user email filled
        if email:
            # Validate each user has different email
            if UserModel.objects.filter(email=email, is_email_verified=True).exclude(id=self.instance.id).exists():
                raise forms.ValidationError(
                    _("Email {email} already registered.".format(email=email)))
        return email


class UserCreationFormExtend(UserCreationForm):
    """ Override user Add form """

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        username = self.cleaned_data.get('username', None)

        # Make user email filled
        if email:
            # Validate each user has different email
            if UserModel.objects.filter(email=email, is_email_verified=True).exclude(username=username).exists():
                raise forms.ValidationError(
                    _("Email {email} already registered.".format(email=email)))
        return email
