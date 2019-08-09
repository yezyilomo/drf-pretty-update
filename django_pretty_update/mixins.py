from rest_framework import serializers


class PrettyUpdate(object):
    def constrain_error_prefix(self, field):
        return f"Error on {field} field: "

    def update_related_field(self, instance, field, value):
        try:
            setattr(instance, field, value)
        except Exception as e:
            message = self.constrain_error_prefix(field) + str(e)
            raise serializers.ValidationError(message)

    def update_many_to_many_ralated_field(self, instance, field, value):
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

    def update_one_to_many_ralated_field(self, instance, field, value):
        if isinstance(value, dict):
            obj = getattr(instance, field)
            for operator in value:
                if operator == "delete":
                    try:
                        obj.filter(pk__in=value[operator]).delete()
                    except Exception as e:
                        message = self.constrain_error_prefix(field) + str(e)
                        raise serializers.ValidationError(message)
                else:
                    message = (
                        f"{operator} is an invalid operator, "
                        "allowed operators are 'add' and 'delete'"
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

    def filter_fields(self, data):
        fields = {
            "simple_related": {},
            "many_related": {}
        }
        for field, value in data.items():
            field_type = self.get_fields()[field]
            if isinstance(field_type, serializers.Serializer):
                fields["simple_related"].update({field+"_id": value})
            elif isinstance(field_type, serializers.ListSerializer):
                fields["many_related"].update({field: value})
            else:
                pass
        return fields

    def create_obj(self, validated_data, simple_related_fields):
        obj = self.Meta.model.objects.create(
            **validated_data,
            **simple_related_fields
        )
        return obj

    def update_simple_related_fields(self, instance, simple_related_fields):
        for field, value in simple_related_fields.items():
            self.update_related_field(instance, field, value)

    def update_many_related_fields(self, instance, many_related_fields):
        for field, value in many_related_fields.items():
            relation = getattr(instance, field).__class__.__name__
            if relation == "ManyRelatedManager":
                self.update_many_to_many_ralated_field(instance, field, value)
            if relation == "RelatedManager":
                self.update_one_to_many_ralated_field(instance, field, value)

    def pretty_update(self, instance, data):
        fields = self.filter_fields(data)
        simple_related_fields = fields["simple_related"]
        many_related_fields = fields["many_related"]
        self.update_simple_related_fields(instance, simple_related_fields)
        self.update_many_related_fields(instance, many_related_fields)

    def create(self, validated_data):
        """Pretty create """
        request = self.context.get('request')
        data = request.data
        fields = self.filter_fields(data)
        simple_related_fields = fields["simple_related"]
        # Validate simple related fields
        obj = self.create_obj(validated_data, simple_related_fields)
        many_related_fields = fields["many_related"]
        # Validate many related fields
        self.update_many_related_fields(obj, many_related_fields)
        return obj

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
