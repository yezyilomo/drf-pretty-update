from rest_framework.serializers import (
    Serializer, ListSerializer, 
    ValidationError, PrimaryKeyRelatedField
)

from .exceptions import InvalidOperation
from .operations import ADD, CREATE, REMOVE, UPDATE


CREATE_SUPPORTED_OPERATIONS = (ADD, CREATE)
UPDATE_SUPPORTED_OPERATIONS = (ADD, CREATE, REMOVE, UPDATE)

class _ReplaceableField(object):
    pass

class _WritableField(object):
    pass

def BaseNestedFieldSerializerFactory(*args, 
                                     pk=False, 
                                     create_ops=[ADD, CREATE], 
                                     update_ops=[ADD, CREATE, REMOVE, UPDATE],
                                     serializer=None, 
                                     **kwargs):
    base_class = _ReplaceableField if pk else _WritableField
    
    if not set(create_ops).issubset(set(CREATE_SUPPORTED_OPERATIONS)):
        msg = (
            "Invalid create operation, Supported operations are " +
            ", ".join(CREATE_SUPPORTED_OPERATIONS)
        )
        raise InvalidOperation(msg)

    if not set(update_ops).issubset(set(UPDATE_SUPPORTED_OPERATIONS)):
        msg = (
            "Invalid update operation, Supported operations are " +
            ", ".join(UPDATE_SUPPORTED_OPERATIONS)
        )
        raise InvalidOperation(msg)

    class BaseNestedFieldListSerializer(ListSerializer, base_class):
        def validate_pk_list(self, pks):
            queryset = self.child.Meta.model.objects.all()
            validator = PrimaryKeyRelatedField(
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
            return self.validate_pk_list(data)

        def validate_create_list(self, data):
            return self.validate_data_list(data)
    
        def validate_remove_list(self, data):
            return self.validate_pk_list(data)
    
        def validate_update_list(self, data):
            # Obtain pks & data then
            if isinstance(data, dict):
                self.validate_pk_list(data.keys())
                self.validate_data_list(list(data.values()))
            else:
                raise ValidationError(
                    "Expected data of form {'pk': 'data'..}"
                )

        def create_data_is_valid(self, data):
            if (isinstance(data, dict) and 
                    set(data.keys()).issubset(create_ops)):
                return True
            return False

        def data_for_create(self, data):
            validate = {
                ADD: self.validate_add_list,
                CREATE: self.validate_create_list, 
            }

            if self.create_data_is_valid(data):
                for operation, values in data.items():
                    validate[operation](values)
                return data
            else:
                op_list =list(map(lambda op: "'" + op + "'", create_ops))
                msg = (
                    "Expected data of form " +
                    "{" + ": [..], ".join(op_list) + ": [..]}"
                )
                raise ValidationError(msg)

        def update_data_is_valid(self, data):
            if (isinstance(data, dict) and 
                    set(data.keys()).issubset(update_ops)):
                return True
            return False

        def data_for_update(self, data):
            validate = {
                ADD: self.validate_add_list,
                CREATE: self.validate_create_list, 
                REMOVE: self.validate_remove_list, 
                UPDATE: self.validate_update_list,
            }

            if self.update_data_is_valid(data):
                for operation, values in data.items():
                    validate[operation](values)
                return data
            else:
                op_list =list(map(lambda op: "'" + op + "'", update_ops))
                msg = (
                    "Expected data of form " +
                    "{" + ": [..], ".join(op_list) + ": [..]}"
                )
                raise ValidationError(msg)

        def to_internal_value(self, data):
            request = self.context.get('request')
            context={"request": request}
            if  request.method in ["PUT", "PATCH"]:
                return self.data_for_update(data)

            if request.method in ["POST"]:
                return self.data_for_create(data)

            parent_serializer = serializer(
                data=data, 
                many=True, 
                context=context
            )
            parent_serializer.is_valid(raise_exception=True)
            return parent_serializer.validated_data

        def __repr__(self):
            return (
                "BaseNestedField(serializer=%s, many=True)" % 
                (serializer.__name__, )
            )

    class BaseNestedFieldSerializer(serializer, base_class):
        class Meta(serializer.Meta):
            list_serializer_class = BaseNestedFieldListSerializer

        def validate_pk_based_nested(self, data):
            queryset = self.Meta.model.objects.all()
            validator = PrimaryKeyRelatedField(
                queryset=queryset,
                many=False
            )
            obj = validator.run_validation(data)
            return data

        def validate_data_based_nested(self, data):
            request = self.context.get("request")
            context={"request": request}
            parent_serializer = serializer(data=data, context=context)
            parent_serializer.is_valid(raise_exception=True)
            return parent_serializer.validated_data

        def to_internal_value(self, data):
            if pk:
                return self.validate_pk_based_nested(data)
            return self.validate_data_based_nested(data)

        def __repr__(self):
            return (
                "BaseNestedField(serializer=%s, many=False)" % 
                (serializer.__name__, )
            )

    kwargs.update({"read_only": False, "write_only": False})
    return {
        "serializer_class": BaseNestedFieldSerializer,
        "list_serializer_class": BaseNestedFieldListSerializer,
        "args": args,
        "kwargs": kwargs
    }



def NestedFieldWraper(*args, **kwargs):
    factory = BaseNestedFieldSerializerFactory(*args, **kwargs)
    serializer = kwargs["serializer"]

    class NestedListSerializer(factory["list_serializer_class"]):
        def __repr__(self):
            return (
                "NestedField(serializer=%s, many=False)" % 
                (serializer.__name__, )
            )


    class NestedSerializer(factory["serializer_class"]):
        class Meta(factory["serializer_class"].Meta):
            list_serializer_class = NestedListSerializer

        def __repr__(self):
            return (
                "NestedField(serializer=%s, many=False)" % 
                (serializer.__name__, )
            )

            
    return NestedSerializer(
        *factory["args"],
        **factory["kwargs"]
    )

def NestedField(serializer=None, *args, **kwargs):
    return NestedFieldWraper(serializer=serializer, *args, **kwargs)
