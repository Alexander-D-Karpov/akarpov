import html

from akarpov.files.models import File

language_previews = {
    "jsx": "javascript",
    "js": "javascript",
    "tsx": "typescript",
    "ts": "typescript",
    "css": "css",
    "py": "python",
    "go": "go",
    "java": "java",
    "php": "php",
    "cs": "csharp",
    "swift": "swift",
    "r": "r",
    "rb": "ruby",
    "c": "c",
    "cpp": "cpp",
    "mlx": "matlab",
    "scala": "scala",
    "sc": "scala",
    "sql": "sql",
    "rs": "rust",
    "pl": "perl",
    "PL": "perl",
    "htm": "html",
}


def view(file: File) -> (str, str):
    extension = file.file.path.split(".")[-1]
    if extension in language_previews:
        extension = language_previews[extension]
    static = f"""
    <meta property="og:title" content="{file.name}" />
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-light.min.css">
    """
    content = "<div class='col-auto'><pre>"
    with file.file.open("r") as f:
        lines = f.readlines()
    for line in lines:
        content += (
            f"""<div class='code language-{extension}'>{html.escape(line)}</div>"""
        )
    content += (
        """</pre></div>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
      """
        + f"""
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/{extension}.min.js"></script>
      """
        + """
      <script>
      hljs.configure({ ignoreUnescapedHTML: true })
      document.querySelectorAll('div.code').forEach(el => {
          hljs.highlightElement(el);
        });
      </script>
    """
    )

    return static, content


def meta(file: File):
    description = ""
    i = 0
    with file.file.open("r") as f:
        lines = f.readlines()
    for line in lines:
        if i == 0:
            description += line + "\n"
        else:
            description += line + "    "
        i += 1
        if i > 20:
            description += "..."
            break
    url = file.get_absolute_url()
    section = ""
    if file.file_type:
        section = file.file_type.split("/")[0]

    meat_f = f"""
    <meta property="og:type" content="article">
    <meta property="og:title" content="{file.name}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="">
    <meta property="og:description" content="{html.escape(description)}">
    <meta property="article:author" content="{file.user.username}">
    <meta property="article:section" content="{section}">
    <meta property="article:published_time" content="{file.created}">
    <meta property="article:modified_time" content="{file.modified}">
    """
    return meat_f
