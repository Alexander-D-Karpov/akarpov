from akarpov.files.models import File


def view(file: File):
    static = ""
    content = ""
    text = file.content.replace("\t", "    ")
    for line in text.split("\n"):
        content += f"<p class='mt-1'>{line}</p>"
    return static, content
