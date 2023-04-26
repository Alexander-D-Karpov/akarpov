from akarpov.files.models import BaseFileItem, Folder


def delete_folder(folder: Folder):
    for child in BaseFileItem.objects.filter(parent=folder):
        if not child.is_file:
            delete_folder(child)
        else:
            if child.file:
                child.delete()
    folder.delete()
