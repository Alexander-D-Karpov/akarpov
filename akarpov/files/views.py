import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView
from django.views.generic.base import TemplateView

from akarpov.contrib.chunked_upload.exceptions import ChunkedUploadError
from akarpov.contrib.chunked_upload.models import ChunkedUpload
from akarpov.contrib.chunked_upload.views import (
    ChunkedUploadCompleteView,
    ChunkedUploadView,
)
from akarpov.files.models import File, Folder
from akarpov.files.previews import extensions, previews


class TopFolderView(LoginRequiredMixin, ListView):
    template_name = "files/list.html"
    paginate_by = 19
    model = File

    def get_queryset(self):
        return File.objects.filter(user=self.request.user, folder__isnull=True)

    def get_context_data(self, **kwargs):
        contex = super().get_context_data(**kwargs)
        contex["folders"] = Folder.objects.filter(
            user=self.request.user, parent__isnull=True
        )
        return contex


class FileView(DetailView):
    template_name = "files/view.html"
    model = File
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_perm"] = self.object.user == self.request.user
        static = ""
        content = ""
        if self.object.file_type:
            t1, t2 = self.object.file_type.split("/")
            extension = self.object.file.path.split(".")[-1]
            loaded = False
            if t1 in previews:
                if t2 in previews[t1]:
                    static, content = previews[t1][t2](self.object)
                    loaded = True
            if not loaded and extension in extensions:
                static, content = extensions[extension](self.object)
        context["preview_static"] = static
        context["preview_content"] = content
        return context


files_view = FileView.as_view()


class DeleteFileView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        file = get_object_or_404(File, slug=kwargs["slug"])
        if file.user == self.request.user:
            file.delete()
        return reverse("files:main")


delete_file_view = DeleteFileView.as_view()


class FileFolderView(DetailView):
    template_name = "files/folder.html"
    model = Folder
    slug_field = "slug"


folder_view = FileFolderView.as_view()


class ChunkedUploadDemo(LoginRequiredMixin, TemplateView):
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
        self.message = {}

    model = ChunkedUpload

    def check_permissions(self, request):
        if not self.request.user.is_authenticated:
            raise ChunkedUploadError(
                403, message="you are not allowed to access this page"
            )

    def on_completion(self, uploaded_file, request):
        if uploaded_file.size <= request.user.left_file_upload:
            f = File.objects.create(
                user=request.user, file=uploaded_file, name=uploaded_file.name
            )
            request.user.left_file_upload -= uploaded_file.size
            request.user.save()
            self.message = {
                "message": f"File {f.file.name.split('/')[-1]} successfully uploaded",
                "status": True,
            }
        else:
            self.message = {
                "message": "File is too large, please increase disk space",
                "status": False,
            }
        if os.path.isfile(uploaded_file.file.path):
            os.remove(uploaded_file.file.path)

    def get_response_data(self, chunked_upload, request):
        return self.message
