import django_tables2 as tables

from akarpov.files.models import File


class FileTable(tables.Table):
    name = tables.columns.Column("name", linkify=True)
    folder = tables.columns.Column(
        linkify=True, accessor="parent", verbose_name="Folder"
    )
    file = tables.columns.FileColumn(
        linkify=True, accessor="file_obj", verbose_name="File"
    )

    class Meta:
        model = File
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            "name",
            "created",
            "modified",
            "views",
            "downloads",
            "folder",
            "private",
            "file",
            "file_type",
        )
