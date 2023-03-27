from django.views.generic import DetailView
from django.views.generic.base import TemplateView

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
    model = File
    field_name = "the_file"

    def check_permissions(self, request):
        # Allow non authenticated users to make uploads
        pass


class MyChunkedUploadCompleteView(ChunkedUploadCompleteView):
    model = File

    def check_permissions(self, request):
        # Allow non authenticated users to make uploads
        pass

    def on_completion(self, uploaded_file, request):
        # Do something with the uploaded file. E.g.:
        # * Store the uploaded file on another model:
        # SomeModel.objects.create(user=request.user, file=uploaded_file)
        # * Pass it as an argument to a function:
        # function_that_process_file(uploaded_file)
        pass

    def get_response_data(self, chunked_upload, request):
        return {
            "message": (
                "You successfully uploaded '%s' (%s bytes)!"
                % (chunked_upload.filename, chunked_upload.offset)
            )
        }
