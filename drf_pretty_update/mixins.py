from rest_framework.serializers import (
    Serializer, ListSerializer, 
    ValidationError
)

from .operations import ADD, CREATE, REMOVE, UPDATE
from .fields import _ReplaceableField, _WritableField


class NestedCreateMixin(object):
    """ Create Mixin """
    def create_replaceable_simple_related(self, data):
        # data format {field: pk}
        objs = {}
        for field, pk in data.items():
            model = self.get_fields()[field].Meta.model
            obj = model.objects.get(pk=pk)
            objs.update({field: obj})
        return objs

    def create_writable_simple_related(self, data):
        # data format {field: {sub_field: value}}
        request = self.context.get("request")
        context={"request": request}
        objs = {}
        for field, value in data.items():
            child = type(self.get_fields()[field])
            serializer = child(data=value, context=context)
            m=serializer.is_valid()
            obj = serializer.save()
            objs.update({field: obj})
        return objs

    def bulk_create_objs(self, field, data):
        pks = []
        request = self.context.get("request")
        context={"request": request}
        model = self.get_fields()[field].child.Meta.model
        child = type(self.get_fields()[field].child)
        for values in data:
            serializer = child(data=values, context=context)
            serializer.is_valid()
            obj = serializer.save()
            pks.append(obj.pk)
        return pks

    def create_many_related(self, instance, data):
        # data format {field: {
        # ADD: [pks], 
        # CREATE: [{sub_field: value}]
        # }}
        fields_pks = {}
        for field, values in data.items():
            for operation in values:
                if operation == ADD:
                    obj = getattr(instance, field)
                    pks = values[operation]
                    obj.set(pks)
                    fields_pks.update({field: pks})
                elif operation == CREATE:
                    obj = getattr(instance, field)
                    pks = self.bulk_create_objs(field, values[operation])
                    obj.set(pks)
                    fields_pks.update({field: pks})
        return fields_pks

    def create(self, validated_data):
        fields = {
            "simple_related": { 
                "replaceable": {},
                "writable": {}
            }, 
            "many_related": {}
        }
        data = {**validated_data}
        for field in data:
            field_type = self.get_fields()[field]
            if isinstance(field_type, Serializer):
                if isinstance(field_type, _ReplaceableField):
                    value = validated_data.pop(field)
                    fields["simple_related"]["replaceable"] \
                        .update({field: value})
                elif isinstance(field_type, _WritableField):
                    value = validated_data.pop(field)
                    fields["simple_related"]["writable"]\
                        .update({field: value})
            elif (isinstance(field_type, ListSerializer) and 
                    (isinstance(field_type, _WritableField) or 
                    isinstance(field_type, _ReplaceableField))):
                value = validated_data.pop(field)
                fields["many_related"].update({field: value})
            else:
                pass

        simple_related = {
            **self.create_replaceable_simple_related(
                fields["simple_related"]["replaceable"]
            ),
            **self.create_writable_simple_related(
                fields["simple_related"]["writable"]
            )
        }

        obj = super().create({**validated_data, **simple_related})
        
        self.create_many_related(
            obj, 
            fields["many_related"]
        )
        
        return obj


class NestedUpdateMixin(object):
    """ Update Mixin """
    def constrain_error_prefix(self, field):
        return f"Error on {field} field: "

    def update_replaceable_simple_related(self, instance, data):
        # data format {field: pk}
        objs = {}
        for field, pk in data.items():
            model = self.get_fields()[field].Meta.model
            child_obj = model.objects.get(pk=pk)
            setattr(instance, field, child_obj)
            instance.save()
            objs.update({field: instance})
        return objs

    def update_writable_simple_related(self, instance, data):
        # data format {field: {sub_field: value}}
        request = self.context.get("request")
        context={"request": request}
        objs = {}
        for field, values in data.items():
            sub_obj = getattr(instance, field)
            child = type(self.get_fields()[field])
            serializer = child(sub_obj, data=values, context=context)
            serializer.is_valid()
            serializer.save()
            objs.update({field: sub_obj})
        return objs

    def bulk_create_many_related(self, field, instance, data):
        pks = []
        request = self.context.get("request")
        context={"request": request}
        sub_obj = getattr(instance, field)
        child = type(self.get_fields()[field].child)
        for values in data:
            serializer = child(data=values, context=context)
            serializer.is_valid()
            obj = serializer.save()
            pks.append(obj.pk)
        sub_obj.add(*pks)
        return pks

    def bulk_update_many_related(self, field, instance, data):
        # {pk: {sub_field: values}}
        objs = []
        request = self.context.get("request")
        context={"request": request}
        model = self.get_fields()[field].child.Meta.model
        child = type(self.get_fields()[field].child)
        for pk, values in data.items():
            obj = model.objects.get(pk=pk)
            serializer = child(obj, data=values, context=context)
            serializer.is_valid()
            obj = serializer.save()
            objs.append(obj)
        return objs

    def update_many_related(self, instance, data):
        # data format {field: {
        # ADD: [{sub_field: value}], 
        # CREATE: [{sub_field: value}], 
        # REMOVE: [pk],
        # UPDATE: {pk: {sub_field: value}} 
        # }}
        for field, values in data.items():
            for operation in values:
                if operation == ADD:
                    obj = getattr(instance, field)
                    pks = values[operation]
                    try:
                        obj.add(*pks)
                    except Exception as e:
                        msg = self.constrain_error_prefix(field) + str(e)
                        raise ValidationError(msg)
                elif operation == CREATE:
                    self.bulk_create_many_related(
                        field, 
                        instance, 
                        values[operation]
                    )
                elif operation == REMOVE:
                    obj = getattr(instance, field)
                    pks = values[operation]
                    try:
                        obj.remove(*pks)
                    except Exception as e:
                        msg = self.constrain_error_prefix(field) + str(e)
                        raise ValidationError(msg)
                elif operation == UPDATE:
                    self.bulk_update_many_related(
                        field, 
                        instance, 
                        values[operation]
                    )
                else:
                    message = (
                        f"{operation} is an invalid operation, "
                    )
                    raise ValidationError(message)
        return instance

    def update(self, instance, validated_data):
        fields = {
            "simple_related": { 
                "replaceable": {},
                "writable": {}
            },
            "many_related": {}
        }
        data = {**validated_data}
        for field in data:
            field_type = self.get_fields()[field]
            if isinstance(field_type, Serializer):
                if isinstance(field_type, _ReplaceableField):
                    value = validated_data.pop(field)
                    fields["simple_related"]["replaceable"] \
                        .update({field: value})
                elif isinstance(field_type, _WritableField):
                    value = validated_data.pop(field)
                    fields["simple_related"]["writable"] \
                        .update({field: value})
            elif (isinstance(field_type, ListSerializer) and
                    (isinstance(field_type, _WritableField) or 
                    isinstance(field_type, _ReplaceableField))):
                value = validated_data.pop(field)
                fields["many_related"].update({field: value})
            else:
                pass

        self.update_replaceable_simple_related(
            instance,
            fields["simple_related"]["replaceable"]
        )
        self.update_writable_simple_related(
            instance,
            fields["simple_related"]["writable"]
        )

        self.update_many_related(
            instance,
            fields["many_related"]
        )

        return super().update(instance, validated_data)