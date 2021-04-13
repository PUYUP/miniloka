from django.db.models.query import QuerySet
from rest_framework import serializers


class CleanValidateMixin(serializers.ModelSerializer):
    def validate(self, attrs):
        # exclude all field with type list or dict
        attr = {
            x: attrs.get(x) for x in list(attrs) 
            if not isinstance(attrs.get(x), list) and not isinstance(attrs.get(x), dict)
        }

        # add current instance value
        if not self.instance:
            instance = self.Meta.model(**attr)
            if hasattr(instance, 'clean'):
                instance.clean(**self.context)
        else:
            if isinstance(self.instance, QuerySet):
                uuid = attrs.get('uuid')
                instance = next((x for x in self.instance if x.uuid == uuid), None)
                
                if instance is not None:
                    for x in attr:
                        setattr(instance, x, attr.get(x))
                    instance.clean(**self.context)
            else:
                for x in attr:
                    setattr(self.instance, x, attr.get(x))
                self.instance.clean(**self.context)

        return attrs
    