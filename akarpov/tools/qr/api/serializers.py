from rest_framework import serializers

from akarpov.tools.qr.models import QR
from akarpov.tools.qr.services import simple


class QRSerializer(serializers.ModelSerializer):
    class Meta:
        model = QR
        fields = ["id", "body", "image"]
        extra_kwargs = {
            "id": {"read_only": True},
            "body": {"write_only": True},
            "image": {"read_only": True},
        }

    def create(self, validated_data):
        user = self.context["request"].user.is_authenticated if self.context["request"].user else None
        qr = simple.run(words=validated_data["body"], user=user)
        return qr
