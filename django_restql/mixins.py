from rest_framework import serializers


class PrettyUpdate(object):
    def constrain_error_prefix(self, field):
        return f"Error on {field} field: "

    def update_related_field(self, instance, field, value):
        try:
            setattr(instance, field+"_id", value)
        except Exception as e:
            message = self.constrain_error_prefix(field) + str(e)
            raise serializers.ValidationError(message)

    def update_many_ralated_field(self, instance, field, value):
        if isinstance(value, dict):
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
        elif isinstance(value, list):
            try:
                getattr(instance, field).set(value)
            except Exception as e:
                message = self.constrain_error_prefix(field) + str(e)
                raise serializers.ValidationError(message)
        else:
            message = (
                f"{field} value must be of type list or dict "
                f"and not {type(value).__name__}"
            )
            raise serializers.ValidationError(message)

    def pretty_update(self, instance, data):
        for field in data:
            field_type = self.get_fields()[field]
            if isinstance(field_type, serializers.Serializer):
                self.update_related_field(instance, field, data[field])
            elif isinstance(field_type, serializers.ListSerializer):
                self.update_many_ralated_field(instance, field, data[field])
            else:
                pass

    def update(self, instance, validated_data):
        """Pretty update """
        request = self.context.get('request')
        data = request.data
        self.pretty_update(instance, data)
        try:
            return super().update(instance, validated_data)
        except Exception as e:
            message = str(e)
            raise serializers.ValidationError(e)
