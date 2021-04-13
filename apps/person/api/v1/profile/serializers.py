import os
import base64

from django.db import transaction
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.files.base import ContentFile

from rest_framework import serializers
from utils.generals import get_model

Profile = get_model('person', 'Profile')


def handle_upload_profile_picture(instance, file, is_original=False):
    if instance and file:
        name, ext = os.path.splitext(file.name)
        username = instance.user.username

        if is_original:
            instance.picture_original.save('%s_original_%s' % (username, ext), file, save=False)
            instance.save(update_fields=['picture_original'])
        else:
            instance.picture.save('%s%s' % (username, ext), file, save=False)
            instance.save(update_fields=['picture'])


def base64_to_file(picture_base64):
    picture_format, picture_imgstr = picture_base64.split(';base64,') 
    picture_ext = picture_format.split('/')[-1] 
    picture_file = ContentFile(base64.b64decode(picture_imgstr), name='temp.' + picture_ext)
    return picture_file


def is_base64(str):
    try:
        base64.b64decode(str)
        return True
    except Exception as e:
        return False


# User profile serializer
class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False)
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        exclude = ('user', 'id', 'create_at', 'update_at',)

    def get_url(self, obj):
        request = self.context.get('request')
        url = reverse('person_api:user-detail', kwargs={'uuid': obj.user.uuid})

        return request.build_absolute_uri(url + 'profile/')

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['gender_display'] = value.get_gender_display()
        return ret

    def to_internal_value(self, data):
        # accept File and Base64
        picture = data.get('picture', None)
        picture_original = data.get('picture_original', None)
        picture_has_changed = data.get('picture_has_changed', False)
        picture_has_removed = data.get('picture_has_removed', False)

        # bring back base64 to file
        if picture and isinstance(picture, str) and is_base64(picture):
            data['picture'] = base64_to_file(picture)

        if picture_original and isinstance(picture_original, str) and is_base64(picture_original):
            data['picture_original'] = base64_to_file(picture_original)

        data = super().to_internal_value(data)

        # user select new picture?
        if picture_has_changed:
            data['picture_has_changed'] = picture_has_changed

        # is picture changed?
        if picture :
            data['has_picture'] = True

        # is picture remove?
        if picture_has_removed:
            data['picture_has_removed'] = True
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request', None)

        # upload picture / avatar use celery task
        picture = validated_data.pop('picture', None)
        picture_original = validated_data.pop('picture_original', None)
        picture_has_changed = validated_data.pop('picture_has_changed', False)
        picture_has_removed = validated_data.pop('picture_has_removed', False)
        has_picture = validated_data.pop('has_picture', False)

        # only execute if update has picture
        if has_picture or picture_has_removed:
            # cropped picture
            if picture:
                fsize = picture.size
                fname = picture.name

                # max size 2.5 MB
                if fsize > 312500:
                    raise serializers.ValidationError(_("Maksimal ukuran file 2.5 MB. Ukuran file avatar Anda %d MB" % (fsize/10000)))

                # only accept JPG, JPEG & PNG
                if not fname.endswith('.jpg') and not fname.endswith('.jpeg') and not fname.endswith('.png'):
                    raise serializers.ValidationError(_("File hanya boleh .jpg dan .png"))

                file = request.FILES.get('picture', None)
                if file is None:
                    file = picture
                handle_upload_profile_picture(instance, file)
            else:
                # delete picture
                instance.picture.delete(save=True)

            # original picture
            if picture_original and picture_has_changed:
                file = request.FILES.get('picture_original', None)
                if file is None:
                    file = picture_original
                handle_upload_profile_picture(instance, file, True)

            if not picture_original and not picture:
                # delete picture
                instance.picture_original.delete(save=True)

        # fields define in serializer
        field_from_serializer = []
        for k, f in self.fields.items():
            field_name = f.field_name
            if not f.read_only:
                field_from_serializer.append(field_name)

        # fields from model
        field_from_model = []
        for field in instance._meta.fields:
            if field.editable == True and not field.primary_key and not field.is_relation:
                field_from_model.append(field.name)
        
        # non profile fields
        # this time use only from User model
        non_profile_field = list((set(field_from_serializer) ^ set(field_from_model)))
        if len(non_profile_field) > 0:
            # update user instance
            for field in non_profile_field:
                value = validated_data.pop(field, None)
                if value:
                    setattr(instance.user, field, value)
            instance.user.save()

        # real profile instance
        update_fields = list()
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if old_value != value:
                    update_fields.append(key)
                    setattr(instance, key, value)
        
        if update_fields:
            instance.save(update_fields=update_fields)
        return instance
