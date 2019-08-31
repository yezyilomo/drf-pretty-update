from rest_framework import serializers


class _ReplaceableField(object):
    pass

class _WritableField(object):
    pass

def ReplaceableNestedField(*args, serializer=None, **kwargs):
    class List(serializers.ListSerializer, _ReplaceableField):
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

        def __repr__(self):
            return (
                "ReplaceableNestedField(serializer=%s, many=True)" % 
                (serializer.__name__, )
            )


    class ReplaceableNestedFieldSerializer(serializer, _ReplaceableField):
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

        def __repr__(self):
            return (
                "ReplaceableNestedField(serializer=%s, many=False)" % 
                (serializer.__name__, )
            )

    kwargs.update({"read_only": False, "write_only": False})
    return ReplaceableNestedFieldSerializer(*args, **kwargs)


def WritableNestedField(*args, serializer=None, **kwargs):

    class List(serializers.ListSerializer, _WritableField):
        def validate_pk_list(self, pks):
            queryset = self.child.Meta.model.objects.all()
            validator = serializers.PrimaryKeyRelatedField(
                queryset=queryset, 
                many=True
            )
            return validator.run_validation(pks)
    
        def validate_data_list(self, data):
            request = self.context.get('request')
            parent_serializer = serializer(
                data=data, 
                many=True, 
                context={"request": request}
            )
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
                raise serializers.ValidationError(
                    "Expected dict of form {'pk': 'data'..}"
                )

        def to_internal_value(self, data):
            request = self.context.get('request')
            context={"request": request}
            if  request.method in ["PUT", "PATCH"]:
                operations = {
                    "add": self.validate_add_list, 
                    "remove": self.validate_remove_list, 
                    "update": self.validate_update_list
                }
                data_is_dict = isinstance(data, dict)
                input_ops = set(data.keys())
                supported_ops = set(operations.keys())
                data_is_valid = input_ops.issubset(supported_ops)
                if data_is_dict and data_is_valid:
                    for operation in data:
                        operations[operation](data[operation])
                    return data
                else:
                    msg = (
                        "Expected dict of form {'add': [..],"
                        "'remove': [..], 'update': [..] }"
                    )
                    raise serializers.ValidationError(msg)

            parent_serializer = serializer(
                data=data, 
                many=True, 
                context=context
            )
            parent_serializer.is_valid(raise_exception=True)
            return parent_serializer.validated_data

        def __repr__(self):
            return (
                "WritableNestedField(serializer=%s, many=True)" % 
                (serializer.__name__, )
            )

    class WritableNestedFieldSerializer(serializer, _WritableField):

        class Meta(serializer.Meta):
            list_serializer_class = List

        def to_internal_value(self, data):
            request = self.context.get("request")
            context={"request": request}
            parent_serializer = serializer(data=data, context=context)
            parent_serializer.is_valid(raise_exception=True)
            return parent_serializer.validated_data

        def __repr__(self):
            return (
                "WritableNestedField(serializer=%s, many=False)" % 
                (serializer.__name__, )
            )

    kwargs.update({"read_only": False, "write_only": False})
    return WritableNestedFieldSerializer(*args, **kwargs)
