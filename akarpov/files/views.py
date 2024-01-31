import os

import elastic_transport
import structlog
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)
from django_filters.views import FilterView
from django_tables2 import SingleTableView
from django_tables2.export import ExportMixin

from akarpov.common.views import SuperUserRequiredMixin
from akarpov.contrib.chunked_upload.exceptions import ChunkedUploadError
from akarpov.contrib.chunked_upload.models import ChunkedUpload
from akarpov.contrib.chunked_upload.views import (
    ChunkedUploadCompleteView as ChunkedUploadABSCompleteView,
)
from akarpov.contrib.chunked_upload.views import (
    ChunkedUploadView as ChunkedUploadABSView,
)
from akarpov.files.filters import FileFilter
from akarpov.files.forms import FileForm, FolderForm
from akarpov.files.models import BaseFileItem, File, FileReport, Folder
from akarpov.files.previews import extensions, meta, meta_extensions, previews
from akarpov.files.services.folders import delete_folder
from akarpov.files.services.preview import get_base_meta
from akarpov.files.services.search import (
    ByteSearch,
    CaseSensitiveSearch,
    NeuroSearch,
    SimilaritySearch,
)
from akarpov.files.tables import FileTable
from akarpov.notifications.services import send_notification

logger = structlog.get_logger(__name__)

search_classes = {
    "neuro": NeuroSearch,
    "case_sensitive": CaseSensitiveSearch,
    "byte_search": ByteSearch,
    "similarity": SimilaritySearch,
}


class FileFilterView(View):
    def filter(self, queryset):
        if "query" in self.request.GET and "search_type" in self.request.GET:
            query = self.request.GET["query"]
            search_type = self.request.GET["search_type"]
            if not query or not self.request.user.is_authenticated:
                return queryset

            if search_type in search_classes:
                search_instance = search_classes[search_type](
                    queryset=File.objects.filter(user=self.request.user).nocache()
                )
                queryset = search_instance.search(query)
        return queryset


class TopFolderView(LoginRequiredMixin, ListView, FileFilterView):
    template_name = "files/list.html"
    paginate_by = 38
    model = BaseFileItem

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["folder_slug"] = None
        context["folder_form"] = FolderForm()
        context["is_folder_owner"] = True

        # folder path
        context["folders"] = []
        return context

    def get_queryset(self):
        if (
            "query" in self.request.GET
            and "search_type" in self.request.GET
            and self.request.GET["query"]
        ):
            return self.filter(BaseFileItem.objects.none())
        return self.filter(
            BaseFileItem.objects.filter(user=self.request.user, parent__isnull=True)
        )


class FileFolderView(ListView, FileFilterView):
    template_name = "files/folder.html"
    model = BaseFileItem
    paginate_by = 38
    slug_field = "slug"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_paginate_by(self, queryset):
        if self.request.user == self.get_object().user:
            # return 38 items for owner to fit file and folder forms
            return 38
        return 40

    def get_context_data(self, **kwargs):
        folder = self.get_object()
        context = super().get_context_data(**kwargs)
        context["folder_slug"] = folder.slug
        context["folder_form"] = FolderForm()
        context["is_folder_owner"] = self.request.user == self.get_object().user

        # folder path
        context["folders"] = folder.get_top_folders() + [folder]
        return context

    def get_object(self, *args):
        obj = get_object_or_404(Folder, slug=self.kwargs["slug"])
        if self.object:
            return self.object
        self.object = obj
        return obj

    def get_queryset(self):
        folder = self.get_object()

        if (
            "query" in self.request.GET
            and "search_type" in self.request.GET
            and self.request.GET["query"]
        ):
            return self.filter(BaseFileItem.objects.none())
        return BaseFileItem.objects.filter(parent=folder)


folder_view = FileFolderView.as_view()


class FileUpdateView(LoginRequiredMixin, UpdateView):
    model = File
    form_class = FileForm

    def get_object(self, *args):
        file = get_object_or_404(File, slug=self.kwargs["slug"])
        if file.user != self.request.user:
            raise PermissionDenied
        return file

    template_name = "files/form.html"


file_update = FileUpdateView.as_view()


class FolderCreateView(LoginRequiredMixin, CreateView):
    model = Folder
    form_class = FolderForm

    def form_valid(self, form):
        folder = None
        if "slug" in self.kwargs and self.kwargs["slug"]:
            folder = get_object_or_404(Folder, slug=self.kwargs["slug"])
        form.instance.user = self.request.user
        form.instance.parent = folder
        super().form_valid(form)
        if folder:
            return HttpResponseRedirect(
                reverse("files:folder", kwargs={"slug": folder.slug})
            )
        return HttpResponseRedirect(reverse("files:main"))


folder_create = FolderCreateView.as_view()


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
        else:
            if file.notify_user_on_view:
                if self.request.user != file.user:
                    send_notification(
                        "File view",
                        f"File {file.name} was opened",
                        "site",
                        user_id=file.user.id,
                        conformation=True,
                    )
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
        parent = file.parent
        if file.user == self.request.user:
            file.delete()
        if parent:
            return reverse("files:folder", kwargs={"slug": parent.slug})
        return reverse("files:main")


delete_file_view = DeleteFileView.as_view()


class ChunkedUploadView(ChunkedUploadABSView):
    model = ChunkedUpload
    field_name = "the_file"

    def check_permissions(self, request):
        if not self.request.user.is_authenticated:
            raise ChunkedUploadError(
                403, message="you are not allowed to access this page"
            )


class ChunkedUploadCompleteView(ChunkedUploadABSCompleteView):
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
            try:
                f = File.objects.create(
                    user=request.user,
                    file_obj=uploaded_file,
                    name=uploaded_file.name,
                    parent=folder,
                )
                request.user.left_file_upload -= uploaded_file.size
                request.user.save()
                self.message = {
                    "message": f"File {f.file.name.split('/')[-1]} successfully uploaded",
                    "status": True,
                }
            except elastic_transport.ConnectionError:
                self.message = {
                    "message": "Service is down, please try again later or contact support",
                    "status": False,
                }
                logger.error("Elasticsearch is down")
        elif prepared:
            self.message = {
                "message": "File is too large, please increase disk space",
                "status": False,
            }
        if os.path.isfile(uploaded_file.file.path):
            os.remove(uploaded_file.file.path)

    def get_response_data(self, chunked_upload, request):
        return self.message


class FileTableView(LoginRequiredMixin, FilterView, ExportMixin, SingleTableView):
    model = File
    table_class = FileTable
    filterset_class = FileFilter
    template_name = "files/tables.html"
    paginate_by = 200

    def get_queryset(self, **kwargs):
        return File.objects.filter(user=self.request.user)


file_table = FileTableView.as_view()


class ReportFileView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        file = get_object_or_404(File, slug=kwargs["slug"])
        FileReport.objects.create(file=file)
        return reverse("files:view", kwargs={"slug": file.slug})


report_file = ReportFileView.as_view()


class ListFileReports(SuperUserRequiredMixin, ListView):
    model = FileReport
    queryset = FileReport.objects.all()
    template_name = "files/reports.html"


file_report_list = ListFileReports.as_view()


class FolderUpdateView(LoginRequiredMixin, UpdateView):
    model = Folder
    form_class = FolderForm

    def get_object(self, *args):
        file = get_object_or_404(Folder, slug=self.kwargs["slug"])
        if file.user != self.request.user:
            raise PermissionDenied
        return file

    template_name = "files/form.html"


folder_update = FolderUpdateView.as_view()


class DeleteFolderView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        folder = get_object_or_404(Folder, slug=kwargs["slug"])
        parent = folder.parent
        if folder.user == self.request.user:
            delete_folder(folder)
        if parent:
            return reverse("files:folder", kwargs={"slug": parent.slug})
        return reverse("files:main")


delete_folder_view = DeleteFolderView.as_view()


class FileDownloadView(View):
    def get(self, request, slug):
        file = get_object_or_404(File, slug=slug)
        file.downloads += 1
        file.save(update_fields=["downloads"])
        return HttpResponseRedirect(file.file.url)


file_download_view = FileDownloadView.as_view()
