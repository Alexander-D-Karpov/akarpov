from rest_framework import serializers


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class SetUserModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        creator = self.context["request"].user
        obj = self.Meta.model.objects.create(creator=creator, **validated_data)
        return obj
