import copy

from rest_framework.serializers import (
    Serializer, ListSerializer, 
    ValidationError
)

from .operations import ADD, CREATE, REMOVE, UPDATE
from .fields import _ReplaceableField, _WritableField


class NestedCreateMixin(object):
    """ Create Mixin """
    def create_replaceable_foreignkey_related(self, data):
        # data format {field: pk}
        objs = {}
        for field, pk in data.items():
            model = self.get_fields()[field].Meta.model
            obj = model.objects.get(pk=pk)
            objs.update({field: obj})
        return objs

    def create_writable_foreignkey_related(self, data):
        # data format {field: {sub_field: value}}
        request = self.context.get("request")
        context={"request": request}
        objs = {}
        for field, value in data.items():
            # Get serializer class for nested field
            SerializerClass = type(self.get_fields()[field])
            serializer = SerializerClass(data=value, context=context)
            serializer.is_valid()
            obj = serializer.save()
            objs.update({field: obj})
        return objs

    def bulk_create_objs(self, field, data):
        request = self.context.get("request")
        context={"request": request}
        model = self.get_fields()[field].child.Meta.model
        SerializerClass = type(self.get_fields()[field].child)
        pks = []
        for values in data:
            serializer = SerializerClass(data=values, context=context)
            serializer.is_valid()
            obj = serializer.save()
            pks.append(obj.pk)
        return pks

    def create_many_related(self, instance, data):
        # data format {field: {
        # ADD: [pks], 
        # CREATE: [{sub_field: value}]
        # }}
        field_pks = {}
        for field, values in data.items():
            for operation in values:
                if operation == ADD:
                    obj = getattr(instance, field)
                    pks = values[operation]
                    obj.set(pks)
                    field_pks.update({field: pks})
                elif operation == CREATE:
                    obj = getattr(instance, field)
                    pks = self.bulk_create_objs(field, values[operation])
                    obj.set(pks)
                    field_pks.update({field: pks})
        return field_pks

    def create(self, validated_data):
        fields = {
            "foreignkey_related": { 
                "replaceable": {},
                "writable": {}
            }, 
            "many_related": {}
        }

        # Make a partal copy of validated_data so that we can
        # iterate and alter it
        data = copy.copy(validated_data)
        for field in data:
            field_serializer = self.get_fields()[field]
            if isinstance(field_serializer, Serializer):
                if isinstance(field_serializer, _ReplaceableField):
                    value = validated_data.pop(field)
                    fields["foreignkey_related"]["replaceable"] \
                        .update({field: value})
                elif isinstance(field_serializer, _WritableField):
                    value = validated_data.pop(field)
                    fields["foreignkey_related"]["writable"]\
                        .update({field: value})
            elif (isinstance(field_serializer, ListSerializer) and 
                    (isinstance(field_serializer, _WritableField) or 
                    isinstance(field_serializer, _ReplaceableField))):
                value = validated_data.pop(field)
                fields["many_related"].update({field: value})
            else:
                pass

        foreignkey_related = {
            **self.create_replaceable_foreignkey_related(
                fields["foreignkey_related"]["replaceable"]
            ),
            **self.create_writable_foreignkey_related(
                fields["foreignkey_related"]["writable"]
            )
        }

        instance = super().create({**validated_data, **foreignkey_related})
        
        self.create_many_related(
            instance, 
            fields["many_related"]
        )
        
        return instance


class NestedUpdateMixin(object):
    """ Update Mixin """
    def constrain_error_prefix(self, field):
        return f"Error on {field} field: "

    def update_replaceable_foreignkey_related(self, instance, data):
        # data format {field: pk}
        objs = {}
        for field, pk in data.items():
            model = self.get_fields()[field].Meta.model
            nested_obj = model.objects.get(pk=pk)
            setattr(instance, field, nested_obj)
            instance.save()
            objs.update({field: instance})
        return objs

    def update_writable_foreignkey_related(self, instance, data):
        # data format {field: {sub_field: value}}
        request = self.context.get("request")
        context={"request": request}
        objs = {}
        for field, values in data.items():
            # Get serializer class for nested field
            SerializerClass = type(self.get_fields()[field])
            nested_obj = getattr(instance, field)
            serializer = SerializerClass(
                nested_obj, 
                data=values, 
                context=context
            )
            serializer.is_valid()
            serializer.save()
            objs.update({field: nested_obj})
        return objs

    def bulk_create_many_related(self, field, nested_obj, data):
        request = self.context.get("request")
        context={"request": request}
        # Get serializer class for nested field
        SerializerClass = type(self.get_fields()[field].child)
        pks = []
        for values in data:
            serializer = SerializerClass(data=values, context=context)
            serializer.is_valid()
            obj = serializer.save()
            pks.append(obj.pk)
        nested_obj.add(*pks)
        return pks

    def bulk_update_many_related(self, field, nested_obj, data):
        # {pk: {sub_field: values}}
        objs = []
        request = self.context.get("request")
        context={"request": request}
        # Get serializer class for nested field
        SerializerClass = type(self.get_fields()[field].child)
        for pk, values in data.items():
            obj = nested_obj.get(pk=pk)
            serializer = SerializerClass(obj, data=values, context=context)
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
            nested_obj = getattr(instance, field)
            for operation in values:
                if operation == ADD:
                    pks = values[operation]
                    try:
                        nested_obj.add(*pks)
                    except Exception as e:
                        msg = self.constrain_error_prefix(field) + str(e)
                        raise ValidationError(msg)
                elif operation == CREATE:
                    self.bulk_create_many_related(
                        field, 
                        nested_obj, 
                        values[operation]
                    )
                elif operation == REMOVE:
                    pks = values[operation]
                    try:
                        nested_obj.remove(*pks)
                    except Exception as e:
                        msg = self.constrain_error_prefix(field) + str(e)
                        raise ValidationError(msg)
                elif operation == UPDATE:
                    self.bulk_update_many_related(
                        field, 
                        nested_obj, 
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
            "foreignkey_related": { 
                "replaceable": {},
                "writable": {}
            },
            "many_related": {}
        }

        # Make a partal copy of validated_data so that we can
        # iterate and alter it
        data = copy.copy(validated_data)
        for field in data:
            field_serializer = self.get_fields()[field]
            if isinstance(field_serializer, Serializer):
                if isinstance(field_serializer, _ReplaceableField):
                    value = validated_data.pop(field)
                    fields["foreignkey_related"]["replaceable"] \
                        .update({field: value})
                elif isinstance(field_serializer, _WritableField):
                    value = validated_data.pop(field)
                    fields["foreignkey_related"]["writable"] \
                        .update({field: value})
            elif (isinstance(field_serializer, ListSerializer) and
                    (isinstance(field_serializer, _WritableField) or 
                    isinstance(field_serializer, _ReplaceableField))):
                value = validated_data.pop(field)
                fields["many_related"].update({field: value})
            else:
                pass

        self.update_replaceable_foreignkey_related(
            instance,
            fields["foreignkey_related"]["replaceable"]
        )
        self.update_writable_foreignkey_related(
            instance,
            fields["foreignkey_related"]["writable"]
        )

        self.update_many_related(
            instance,
            fields["many_related"]
        )

        return super().update(instance, validated_data)