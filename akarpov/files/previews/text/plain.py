import html

from akarpov.files.models import File
from akarpov.files.previews import text
from akarpov.files.previews.text.common import language_previews


def view(file: File) -> (str, str):
    extension = file.file.path.split(".")[-1]
    if hasattr(text, extension):
        return getattr(text, extension).view(file)
    elif extension in language_previews:
        return text.common.view(file)
    static = f"""
    <meta property="og:title" content="{file.name}" />
    """
    content = "<pre>"
    with file.file.open("r") as f:
        lines = f.readlines()
    for line in lines:
        content += f"""<div class='code language-plaintext'>{html.escape(line)}</div>"""
    content += "</pre>"
    return static, content
