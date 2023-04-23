import os

import structlog
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django.views.generic.base import TemplateView

from akarpov.contrib.chunked_upload.exceptions import ChunkedUploadError
from akarpov.contrib.chunked_upload.models import ChunkedUpload
from akarpov.contrib.chunked_upload.views import (
    ChunkedUploadCompleteView,
    ChunkedUploadView,
)
from akarpov.files.forms import FileForm
from akarpov.files.models import BaseFileItem, File, Folder
from akarpov.files.previews import extensions, meta, meta_extensions, previews
from akarpov.files.services.preview import get_base_meta

logger = structlog.get_logger(__name__)


class TopFolderView(LoginRequiredMixin, ListView):
    template_name = "files/list.html"
    paginate_by = 19
    model = BaseFileItem

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["folder_slug"] = None
        return context

    def get_queryset(self):
        return BaseFileItem.objects.filter(user=self.request.user, parent__isnull=True)


class FileFolderView(ListView):
    template_name = "files/folder.html"
    model = BaseFileItem
    paginate_by = 39
    slug_field = "slug"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_context_data(self, **kwargs):
        folder = self.get_object()
        context = super().get_context_data(**kwargs)
        context["folder_slug"] = folder.slug
        return context

    def get_object(self, *args):
        obj = get_object_or_404(Folder, slug=self.kwargs["slug"])
        if self.object:
            return self.object
        self.object = obj
        return obj

    def get_queryset(self):
        folder = self.get_object()
        return BaseFileItem.objects.filter(parent=folder)


class FileUpdateView(LoginRequiredMixin, UpdateView):
    model = File
    form_class = FileForm

    def get_object(self):
        file = get_object_or_404(File, slug=self.kwargs["slug"])
        if file.user != self.request.user:
            raise PermissionDenied
        return file

    template_name = "files/form.html"


file_update = FileUpdateView.as_view()


class FileView(DetailView):
    template_name = "files/view.html"
    model = File
    slug_field = "slug"

    def dispatch(self, request, *args, **kwargs):
        # redirect if bot
        file = self.get_object()
        useragent = request.META["HTTP_USER_AGENT"].lower()
        if "bot" in useragent:
            if file.file_type and file.file_type.split("/")[0] == "image":
                return HttpResponseRedirect(file.file.url)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        static = ""
        content = ""
        meta_s = ""
        extension = self.object.file.path.split(".")[-1]

        try:
            meta_loaded = False
            if self.object.file_type:
                t1, t2 = self.object.file_type.split("/")
                loaded = False

                # get static and content for file view by mimetype
                if t1 in previews:
                    if t2 in previews[t1]:
                        static, content = previews[t1][t2](self.object)
                        loaded = True
                if not loaded and extension in extensions:
                    static, content = extensions[extension](self.object)

                # get meta tags by mimetype
                if t1 in meta:
                    if t2 in meta[t1]:
                        meta_s = meta[t1][t2](self.object)
                        meta_loaded = True
                if not meta_loaded and extension in meta_extensions:
                    meta_s = meta_extensions[extension](self.object)
            else:
                # get static and content for file view by file extension
                if extension in extensions:
                    static, content = extensions[extension](self.object)
                # get meta tags by file extension
                if extension in meta_extensions:
                    meta_s = meta_extensions[extension](self.object)
                    meta_loaded = True
            if not meta_loaded:
                meta_s = get_base_meta(self.object)
        except Exception as e:
            logger.error(e)

        context = super().get_context_data(**kwargs)
        context["has_perm"] = self.object.user == self.request.user
        context["preview_static"] = static
        context["preview_content"] = content
        context["meta"] = meta_s
        return context


files_view = FileView.as_view()


class DeleteFileView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        file = get_object_or_404(File, slug=kwargs["slug"])
        if file.user == self.request.user:
            file.delete()
        return reverse("files:main")


delete_file_view = DeleteFileView.as_view()


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
        folder = None
        prepared = True
        if "slug" in self.kwargs and self.kwargs["slug"]:
            try:
                folder = Folder.objects.get(slug=self.kwargs["slug"])
                if folder.user != self.request.user:
                    self.message = {
                        "message": "You can't upload to this folder",
                        "status": False,
                    }
                    prepared = False
            except Folder.DoesNotExist:
                self.message = {
                    "message": "Folder doesn't exist",
                    "status": False,
                }
                prepared = False
        if prepared and uploaded_file.size <= request.user.left_file_upload:
            f = File.objects.create(
                user=request.user,
                file_obj=uploaded_file,
                name=uploaded_file.name,
                parent=folder,
            )
            if folder:
                folder.modified = now()
                folder.size += uploaded_file.size
                folder.amount += 1
                folder.save()
            request.user.left_file_upload -= uploaded_file.size
            request.user.save()
            self.message = {
                "message": f"File {f.file.name.split('/')[-1]} successfully uploaded",
                "status": True,
            }
        elif prepared:
            self.message = {
                "message": "File is too large, please increase disk space",
                "status": False,
            }
        if os.path.isfile(uploaded_file.file.path):
            os.remove(uploaded_file.file.path)

    def get_response_data(self, chunked_upload, request):
        return self.message
