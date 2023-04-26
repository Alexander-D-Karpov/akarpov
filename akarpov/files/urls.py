from django.urls import path

from akarpov.files.views import (
    ChunkedUploadCompleteView,
    ChunkedUploadView,
    TopFolderView,
    delete_file_view,
    delete_folder_view,
    file_report_list,
    file_table,
    file_update,
    files_view,
    folder_create,
    folder_update,
    folder_view,
    report_file,
)

app_name = "files"
urlpatterns = [
    path("", TopFolderView.as_view(), name="main"),
    path("table/", file_table, name="table"),
    path("reports/", file_report_list, name="reports"),
    path(
        "api/chunked_upload_complete/",
        ChunkedUploadCompleteView.as_view(),
        name="api_chunked_upload_complete",
    ),
    path(
        "api/chunked_upload_complete/<str:slug>",
        ChunkedUploadCompleteView.as_view(),
        name="api_chunked_upload_complete_folder",
    ),
    path("api/chunked_upload/", ChunkedUploadView.as_view(), name="api_chunked_upload"),
    path("api/folder/create/", folder_create, name="folder_create"),
    path("api/file/report/<str:slug>", report_file, name="file_report"),
    path("api/file/delete/<str:slug>", delete_file_view, name="delete"),
    path("api/folder/create/<str:slug>", folder_create, name="sub_folder_create"),
    path("api/folder/delete/<str:slug>", delete_folder_view, name="folder_delete"),
    path("<str:slug>", files_view, name="view"),
    path("<str:slug>/update", file_update, name="update"),
    path("f/<str:slug>", folder_view, name="folder"),
    path("f/<str:slug>/update", folder_update, name="folder_update"),
]
