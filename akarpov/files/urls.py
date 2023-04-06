from django.urls import path

from akarpov.files.views import (
    ChunkedUploadDemo,
    MyChunkedUploadCompleteView,
    MyChunkedUploadView,
    TopFolderView,
    files_view,
    folder_view,
)

app_name = "files"
urlpatterns = [
    path("", TopFolderView.as_view(), name="main"),
    path("upload", ChunkedUploadDemo.as_view(), name="chunked_upload"),
    path(
        "api/chunked_upload_complete/",
        MyChunkedUploadCompleteView.as_view(),
        name="api_chunked_upload_complete",
    ),
    path(
        "api/chunked_upload/", MyChunkedUploadView.as_view(), name="api_chunked_upload"
    ),
    path("<str:slug>", files_view, name="view"),
    path("f/<str:slug>", folder_view, name="folder"),
]
