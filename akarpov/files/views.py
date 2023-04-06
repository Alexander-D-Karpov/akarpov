import os

from django.views.generic import DetailView
from django.views.generic.base import TemplateView

from akarpov.contrib.chunked_upload.exceptions import ChunkedUploadError
from akarpov.contrib.chunked_upload.models import ChunkedUpload
from akarpov.contrib.chunked_upload.views import (
    ChunkedUploadCompleteView,
    ChunkedUploadView,
)
from akarpov.files.models import File, Folder


class FileView(DetailView):
    template_name = "files/view.html"
    model = File
    slug_field = "slug"


files_view = FileView.as_view()


class FileFolderView(DetailView):
    template_name = "files/folder.html"
    model = Folder
    slug_field = "slug"


folder_view = FileFolderView.as_view()


class ChunkedUploadDemo(TemplateView):
    template_name = "files/upload.html"


class MyChunkedUploadView(ChunkedUploadView):
    model = ChunkedUpload
    field_name = "the_file"

    def check_permissions(self, request):
        if not self.request.user.is_authenticated:
            raise ChunkedUploadError(
                403, message="you are not allowed to access this page"
            )


class MyChunkedUploadCompleteView(ChunkedUploadCompleteView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message = "file is successfully uploaded"

    model = ChunkedUpload

    def check_permissions(self, request):
        if not self.request.user.is_authenticated:
            raise ChunkedUploadError(
                403, message="you are not allowed to access this page"
            )

    def on_completion(self, uploaded_file, request):
        if uploaded_file.size <= request.user.left_file_upload:
            File.objects.create(user=request.user, file=uploaded_file)
            request.user.left_file_upload -= uploaded_file.size
            request.user.save()
        else:
            self.message = "File is too large"
        if os.path.isfile(uploaded_file.file.path):
            os.remove(uploaded_file.file.path)

    def get_response_data(self, chunked_upload, request):
        return {"message": (self.message)}
