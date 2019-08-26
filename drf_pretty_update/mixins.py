from rest_framework import serializers


class ReplaceableField(object):
    pass

class WritableField(object):
    pass

def ReplaceableNestedField(*args, serializer=None, **kwargs):
    class List(serializers.ListSerializer, ReplaceableField):
        def validate_nested(self, data):
            queryset = self.child.Meta.model.objects.all()
            validator = serializers.PrimaryKeyRelatedField(
                queryset=queryset,
                many=True
            )
            obj = validator.run_validation(data)
            return obj

        def to_internal_value(self, data):
            request = self.context.get('request')
            if request.method in ["PUT", "PATCH"]:
                operations = ["add", "remove"]
                if isinstance(data, dict) and set(data.keys()).issubset(set(operations)):
                    pks = [pk for sub_pk in data.values() for pk in sub_pk]
                    self.validate_nested(pks)
                    return data
                else:
                    raise serializers.ValidationError(
                        "Expects dict of form {'add': [..], 'remove': [..]}"
                    )
            self.validate_nested(data)
            return data


    class ReplaceableNestedFieldSerializer(serializer, ReplaceableField):
        class Meta(serializer.Meta):
            list_serializer_class = List

        def run_validation(self, data):
            (is_empty_value, data) = self.validate_empty_values(data)
            if is_empty_value:
                return data
            value = self.to_internal_value(data)
            return value

        def validate_nested(self, data):
            queryset = self.Meta.model.objects.all()
            validator = serializers.PrimaryKeyRelatedField(
                queryset=queryset,
                many=False
            )
            obj = validator.run_validation(data)
            return obj

        def to_internal_value(self, data):
            self.validate_nested(data)
            return data

    return ReplaceableNestedFieldSerializer(*args, **kwargs)


def WritableNestedField(*args, serializer=None, **kwargs):

    class List(serializers.ListSerializer, WritableField):
        def validate_pk_list(self, pks):
            queryset = self.child.Meta.model.objects.all()
            validator = serializers.PrimaryKeyRelatedField(queryset=queryset, many=True)
            return validator.run_validation(pks)
    
        def validate_data_list(self, data):
            parent_serializer = serializer(data=data, many=True)
            parent_serializer.is_valid(raise_exception=True)
            return parent_serializer.validated_data
    
        def validate_add_list(self, data):
            return self.validate_data_list(data)
    
        def validate_remove_list(self, data):
            return self.validate_pk_list(data)
    
        def validate_update_list(self, data):
            # Obtain pks & data then
            if isinstance(data, dict):
                self.validate_pk_list(data.keys())
                self.validate_data_list(list(data.values()))
            else:
                raise serializers.ValidationError("Expected dict of form {'pk': 'data'..}")

        def to_internal_value(self, data):
            request = self.context.get('request')
            if request.method in ["PUT", "PATCH"]:
                operations = {
                    "add": self.validate_add_list, 
                    "remove": self.validate_remove_list, 
                    "update": self.validate_update_list
                }
                data_is_dict = isinstance(data, dict)
                data_is_valid = set(data.keys()).issubset(set(operations.keys()))
                if data_is_dict and data_is_valid:
                    for operation in data:
                        operations[operation](data[operation])
                    return data
                else:
                    raise serializers.ValidationError(
                        "Expected dict of form {'add': [..], 'remove': [..], 'update': [..] }"
                    )

            parent_serializer = serializer(data=data, many=True)
            parent_serializer.is_valid(raise_exception=True)
            return parent_serializer.validated_data


    class WritableNestedFieldSerializer(serializer, WritableField):

        class Meta(serializer.Meta):
            list_serializer_class = List

        def to_internal_value(self, data):
            parent_serializer = serializer(data=data)
            parent_serializer.is_valid(raise_exception=True)
            return parent_serializer.validated_data

    return WritableNestedFieldSerializer(*args, **kwargs)


class NestedModelSerializer(serializers.ModelSerializer):
    def constrain_error_prefix(self, field):
        return f"Error on {field} field: "

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
        objs = {}
        for field, value in data.items():
            child = type(self.get_fields()[field])
            serializer = child(data=value)
            serializer.is_valid()
            obj = serializer.save()
            objs.update({field: obj})
        return objs

    def bulk_create_objs(self, field, data):
        pks = []
        model = self.get_fields()[field].child.Meta.model
        child = type(self.get_fields()[field].child)
        for values in data:
            serializer = child(data=values)
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
            "replaceable_nested_fields": {"simple_related": {}, "many_related": {}},
            "writable_nested_fields": {"simple_related": {}, "many_related": {}}
        }
        data = {**validated_data}
        for field in data:
            field_type = self.get_fields()[field]
            if isinstance(field_type, ReplaceableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["replaceable_nested_fields"]["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["replaceable_nested_fields"]["many_related"].update({field: value})
                else:
                    pass
            elif isinstance(field_type, WritableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["writable_nested_fields"]["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["writable_nested_fields"]["many_related"].update({field: value})
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
        objs = {}
        for field, values in data.items():
            sub_obj = getattr(instance, field)
            child = type(self.get_fields()[field])
            serializer = child(sub_obj, data=values)
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
        sub_obj = getattr(instance, field)
        child = type(self.get_fields()[field].child)
        for values in data:
            serializer = child(data=values)
            serializer.is_valid()
            obj = serializer.save()
            pks.append(obj.pk)
        sub_obj.add(*pks)
        return pks

    def bulk_update_many_related(self, field, instance, data):
        # {pk: {sub_field: values}}
        objs = []
        model = self.get_fields()[field].child.Meta.model
        child = type(self.get_fields()[field].child)
        for pk, values in data.items():
            obj = model.objects.get(pk=pk)
            serializer = child(obj, data=values)
            serializer.is_valid()
            obj = serializer.save()
            objs.append(obj)
        return objs

    def update_writable_many_related(self, instance, data):
        # data format {field: {add: [{sub_field: value}], remove: [pk], update: {pk: {sub_field: value}} }}
        for field, value in data.items():
            for operator in value:
                if operator == "add":
                    self.bulk_create_many_related(field, instance, value[operator])
                elif operator == "remove":
                    obj = getattr(instance, field)
                    try:
                        obj.remove(*value[operator])
                    except Exception as e:
                        message = self.constrain_error_prefix(field) + str(e)
                        raise serializers.ValidationError(message)
                elif operator == "update":
                    self.bulk_update_many_related(field, instance, value[operator])
                else:
                    message = (
                        f"{operator} is an invalid operator, "
                        "allowed operators are 'add' and 'remove'"
                    )
                    raise serializers.ValidationError(message)
        return instance

    def update(self, instance, validated_data):
        fields = {
            "replaceable_nested_fields": {"simple_related": {}, "many_related": {}},
            "writable_nested_fields": {"simple_related": {}, "many_related": {}}
        }
        data = {**validated_data}
        for field in data:
            field_type = self.get_fields()[field]
            if isinstance(field_type, ReplaceableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["replaceable_nested_fields"]["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["replaceable_nested_fields"]["many_related"].update({field: value})
                else:
                    pass
            elif isinstance(field_type, WritableField):
                value = validated_data.pop(field)
                if isinstance(field_type, serializers.Serializer):
                    fields["writable_nested_fields"]["simple_related"].update({field: value})
                elif isinstance(field_type, serializers.ListSerializer):
                    fields["writable_nested_fields"]["many_related"].update({field: value})
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