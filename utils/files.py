import os
import calendar
import time

from django.core.files.storage import FileSystemStorage
from django.template.defaultfilters import slugify

ALLOWED_EXTENSIONS = ['.jpeg', '.jpg', '.png', '.pdf', '.docx']


class FileSystemStorageExtend(FileSystemStorage):
    def generate_filename(self, filename, *args, **kwargs):
        # Format [timestamp]-[entity]-[object_uuid]-[filename].[ext]
        # Output: 12345675-media-99-mountain.jpg
        dirname, filename = os.path.split(filename)
        file_root, file_ext = os.path.splitext(filename)

        instance = kwargs.get('instance', None)
        content_type = slugify(instance.content_type)
        object_uuid = instance.uuid
        timestamp = calendar.timegm(time.gmtime())
        filename = '{0}_{1}_{2}_{3}'.format(
            timestamp, content_type, object_uuid, file_root)

        return os.path.normpath(
            os.path.join(
                dirname, self.get_valid_name(slugify(filename)+file_ext)))


def handle_upload_attachment(instance, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)
        filename_slug = slugify(name)
        model_name = instance.content_type.model

        instance.type = ext
        instance.file.save('%s-%s%s' % (model_name, filename_slug, ext), file, save=False)
        instance.label = instance.file.name
        instance.save(update_fields=['label', 'file', 'type'])
