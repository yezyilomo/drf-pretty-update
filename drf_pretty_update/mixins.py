from rest_framework import serializers

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
            serializer.is_valid()
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

    def create_replaceable_many_related(self, instance, data):
        # data format {field: [pks]}
        objs = {}
        for field, pks in data.items():
            obj = getattr(instance, field)
            model = self.get_fields()[field].child.Meta.model
            obj_queryset = model.objects.filter(pk__in=pks)
            obj.set(pks)
            objs.update({field: obj_queryset})
        return objs

    def create_writable_many_related(self, instance, data):
        # data format {field: [{sub_field: value}]}
        fields_pks = {}
        for field, value in data.items():
            obj = getattr(instance, field)
            pks = self.bulk_create_objs(field, value)
            fields_pks.update({field: pks})
            obj.set(pks)
        return fields_pks

    def create(self, validated_data):
        fields = {
            "replaceable_nested_fields": {
                "simple_related": {}, 
                "many_related": {}
            },
            "writable_nested_fields": {
                "simple_related": {}, 
                "many_related": {}
            }
        }
        data = {**validated_data}
        for field in data:
            field_type = self.get_fields()[field]
            if isinstance(field_type, _ReplaceableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["replaceable_nested_fields"]\
                        ["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["replaceable_nested_fields"]\
                        ["many_related"].update({field: value})
                else:
                    pass
            elif isinstance(field_type, _WritableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["writable_nested_fields"]\
                        ["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["writable_nested_fields"]\
                        ["many_related"].update({field: value})
                else:
                    pass
            else:
                pass

        simple_related = {
            **self.create_replaceable_simple_related(
                fields["replaceable_nested_fields"]["simple_related"]
            ),
            **self.create_writable_simple_related(
                fields["writable_nested_fields"]["simple_related"]
            )
        }

        obj = super().create({**validated_data, **simple_related})
        
        self.create_replaceable_many_related(
            obj, 
            fields["replaceable_nested_fields"]["many_related"]
        )
        
        self.create_writable_many_related(
            obj,
            fields["writable_nested_fields"]["many_related"]
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
            child_obj = self.get_fields()[field].Meta.model.objects.get(pk=pk)
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

    def update_replaceable_many_related(self, instance, data):
        # data format {field: {add: [pk], remove: [pk], delete: [pk]}}
        for field, value in data.items():
            obj = getattr(instance, field)
            for operator in value:
                if operator == "add":
                    try:
                        obj.add(*value[operator])
                    except Exception as e:
                        message = self.constrain_error_prefix(field) + str(e)
                        raise serializers.ValidationError(message)
                elif operator == "remove":
                    try:
                        obj.remove(*value[operator])
                    except Exception as e:
                        message = self.constrain_error_prefix(field) + str(e)
                        raise serializers.ValidationError(message)
                else:
                    message = (
                        f"{operator} is an invalid operator, "
                        "allowed operators are 'add' and 'remove'"
                    )
                    raise serializers.ValidationError(message)
        return instance

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

    def update_writable_many_related(self, instance, data):
        # data format {field: {add: [{sub_field: value}], remove: [pk], update: {pk: {sub_field: value}} }}
        for field, value in data.items():
            for operator in value:
                if operator == "add":
                    self.bulk_create_many_related(
                        field, 
                        instance, 
                        value[operator]
                    )
                elif operator == "remove":
                    obj = getattr(instance, field)
                    try:
                        obj.remove(*value[operator])
                    except Exception as e:
                        msg = self.constrain_error_prefix(field) + str(e)
                        raise serializers.ValidationError(msg)
                elif operator == "update":
                    self.bulk_update_many_related(
                        field, 
                        instance, 
                        value[operator]
                    )
                else:
                    message = (
                        f"{operator} is an invalid operator, "
                        "allowed operators are 'add' and 'remove'"
                    )
                    raise serializers.ValidationError(message)
        return instance

    def update(self, instance, validated_data):
        fields = {
            "replaceable_nested_fields": {
                "simple_related": {}, 
                "many_related": {}
            },
            "writable_nested_fields": {
                "simple_related": {}, 
                "many_related": {}
            }
        }
        data = {**validated_data}
        for field in data:
            field_type = self.get_fields()[field]
            if isinstance(field_type, _ReplaceableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["replaceable_nested_fields"]\
                        ["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["replaceable_nested_fields"]\
                        ["many_related"].update({field: value})
                else:
                    pass
            elif isinstance(field_type, _WritableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["writable_nested_fields"]\
                        ["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["writable_nested_fields"]\
                        ["many_related"].update({field: value})
                else:
                    pass
            else:
                pass

        self.update_replaceable_simple_related(
            instance,
            fields["replaceable_nested_fields"]["simple_related"]
        )
        self.update_writable_simple_related(
            instance,
            fields["writable_nested_fields"]["simple_related"]
        )
        self.update_replaceable_many_related(
            instance, 
            fields["replaceable_nested_fields"]["many_related"]
        )
        self.update_writable_many_related(
            instance,
            fields["writable_nested_fields"]["many_related"]
        )

        return super().update(instance, validated_data)