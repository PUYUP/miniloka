import itertools

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction
from django.http import request
from django.utils.encoding import smart_str

from rest_framework import serializers


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None and fields != '__all__':
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ExcludeFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        exclude_fields = kwargs.pop('exclude_fields', None)

        # Instantiate the superclass normally
        super(ExcludeFieldsModelSerializer, self).__init__(*args, **kwargs)

        if exclude_fields is not None and exclude_fields != '__all__':
            # Drop any fields that are not specified in the `fields` argument.
            for field_name in set(exclude_fields):
                self.fields.pop(field_name)


class WritetableFieldPutMethod(serializers.ModelSerializer):
    """
    Sometime PUT method need field is writetable but we don't want
    break entire function.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        kwargs.pop('fields', None)
        
        # Instantiate the superclass normally
        super(WritetableFieldPutMethod, self).__init__(*args, **kwargs)

        context = kwargs.get('context', dict())
        request = context.get('request', dict())
        request_method = getattr(request, 'method', None)

        if request_method == 'PUT':
            # Extract updated field.
            _fx = [list(item.keys()) for item in kwargs.get('data')]
            _fy = list(itertools.chain.from_iterable(_fx))

            allowed = set(list(dict.fromkeys(_fy)))
            existing = set(self.fields)

            for field_name in existing - allowed:
                self.fields.pop(field_name)

            # Make field editable.
            for field_name in allowed:
                try:
                    self.fields[field_name].read_only = False
                except KeyError:
                    pass


class ListSerializerUpdateMappingField(serializers.ListSerializer):
    @transaction.atomic
    def update(self, instance, validated_data):
        # Maps for uuid->instance and uuid->data item.
        obj_mapping = {obj.uuid: obj for obj in instance}
        data_mapping = {item.get('uuid', index): item for index, item in enumerate(validated_data)}

        # Perform creations and updates.
        ret = []
        for obj_uuid, data in data_mapping.items():
            obj = obj_mapping.get(obj_uuid, None)

            if obj is None:
                ret.append(self.child.create(data))
            else:
                ret.append(self.child.update(obj, data))

        # Perform deletions.
        for obj_uuid, obj in obj_mapping.items():
            if obj_uuid not in data_mapping:
                obj.delete()

        return ret


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        request = self.context.get('request')
        queryset = self.get_queryset()
        model = queryset.model

        try:
            instance, _created = model.objects \
                .get_or_create(**{self.slug_field: data}, defaults={'user': request.user})
            return instance
        except MultipleObjectsReturned:
            instance = model.objects.filter(**{self.slug_field: data}).first()
            return instance
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_str(data))
        except (TypeError, ValueError):
            self.fail('invalid')
