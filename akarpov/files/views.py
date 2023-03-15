from django.views.generic import DetailView

from akarpov.files.models import BaseFile, Folder


class FileView(DetailView):
    template_name = "files/view.html"
    model = BaseFile
    slug_field = "slug"


files_view = FileView.as_view()


class FileFolderView(DetailView):
    template_name = "files/folder.html"
    model = Folder
    slug_field = "slug"


folder_view = FileFolderView.as_view()
