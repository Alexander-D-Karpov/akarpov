from rest_framework import serializers

from akarpov.utils.models import get_model_user_field


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class SetUserModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        if self.context["request"].user.is_authenticated:
            creator = self.context["request"].user
        else:
            creator = None
        validated_data[
            get_model_user_field(
                self.Meta.model._meta.app_label, self.Meta.model._meta.model_name
            )
        ] = creator
        try:
            obj = self.Meta.model.objects.create(**validated_data)
        except TypeError:
            raise serializers.ValidationError(
                {"detail": "You need to login to create this object"}
            )
        return obj
