from django.urls import path
from drf_chunked_upload.views import ChunkedUploadView

urlpatterns = [
    path("upload/", ChunkedUploadView.as_view(), name="chunked_upload"),
]
