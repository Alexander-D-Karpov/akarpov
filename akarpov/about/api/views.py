from rest_framework import generics, permissions, response

from akarpov.about.api.serializers import StatusSerializer


class PingAPIView(generics.GenericAPIView):
    serializer_class = StatusSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return response.Response(data={"status": "pong"})
