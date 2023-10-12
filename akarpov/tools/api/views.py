from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from akarpov.tools.api.serializers import URLPathSerializer
from akarpov.tools.api.services import get_api_path_by_url


class RetrieveAPIUrlAPIView(generics.GenericAPIView):
    serializer_class = URLPathSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        path, k_args = get_api_path_by_url(self.kwargs["path"])
        if not path:
            raise NotFound
        return Response(data={"path": path, "kwargs": k_args})
