import textract

from akarpov.files.models import File


def view(file: File):
    static = ""
    content = ""
    text = (
        textract.process(file.file.path, extension="odt", output_encoding="utf8")
        .decode("utf8")
        .replace("\t", "    ")
    )
    for line in text.split("\n"):
        content += f"<p class='mt-1'>{line}</p>"
    return static, content
