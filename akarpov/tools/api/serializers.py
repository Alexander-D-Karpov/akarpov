from rest_framework import serializers


class URLPathSerializer(serializers.Serializer):
    path = serializers.URLField()
    kwargs = serializers.DictField(help_text="{'slug': 'str', 'pk': 'int'}")
