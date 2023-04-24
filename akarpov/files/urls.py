from django.urls import path

from akarpov.files.views import (
    MyChunkedUploadCompleteView,
    MyChunkedUploadView,
    TopFolderView,
    delete_file_view,
    file_table,
    file_update,
    files_view,
    folder_create,
    folder_view,
)

app_name = "files"
urlpatterns = [
    path("", TopFolderView.as_view(), name="main"),
    path("table/", file_table, name="table"),
    path(
        "api/chunked_upload_complete/",
        MyChunkedUploadCompleteView.as_view(),
        name="api_chunked_upload_complete",
    ),
    path(
        "api/chunked_upload_complete/<str:slug>",
        MyChunkedUploadCompleteView.as_view(),
        name="api_chunked_upload_complete_folder",
    ),
    path(
        "api/chunked_upload/", MyChunkedUploadView.as_view(), name="api_chunked_upload"
    ),
    path("api/folder/create/", folder_create, name="folder_create"),
    path("api/folder/create/<str:slug>", folder_create, name="sub_folder_create"),
    path("<str:slug>", files_view, name="view"),
    path("<str:slug>/update", file_update, name="update"),
    path("<str:slug>/delete", delete_file_view, name="delete"),
    path("f/<str:slug>", folder_view, name="folder"),
]
