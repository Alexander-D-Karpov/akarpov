import html

from akarpov.files.models import File


def view(file: File) -> (str, str):
    static = f"""
    <meta property="og:title" content="{file.name}" />
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-light.min.css">
    """
    content = "<div class='col-auto'><pre>"
    with file.file.open("r") as f:
        lines = f.readlines()
    style = False
    js = False
    for line in lines:
        if "<style" in line and "</style>" not in line:
            style = True
        elif "</style>" in line:
            style = False

        if "<script" in line and "</script>" not in line:
            js = True
        elif "</script>" in line:
            js = False

        if style:
            content += f"""<div class='code language-css'>{html.escape(line)}</div>"""
        elif js:
            content += (
                f"""<div class='code language-javascript'>{html.escape(line)}</div>"""
            )
        else:
            content += f"""<div class='code language-html'>{html.escape(line)}</div>"""

    content += """</pre></div>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/javascipt.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/html.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/css.min.js"></script>
      <script>
      hljs.configure({ ignoreUnescapedHTML: true })
      document.querySelectorAll('div.code').forEach(el => {
          hljs.highlightElement(el);
        });
      </script>
    """

    return static, content


def meta(file: File):
    descr = ""
    i = 0
    with file.file.open("r") as f:
        lines = f.readlines()
    for line in lines:
        if i == 0:
            descr += line + "\n"
        else:
            descr += line + "    "
        i += 1
        if i > 20:
            descr += "..."
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
    <meta property="og:description" content="{html.escape(descr)}">
    <meta property="article:author" content="{file.user.username}">
    <meta property="article:section" content="{section}">
    <meta property="article:published_time" content="{file.created}">
    <meta property="article:modified_time" content="{file.modified}">
    """
    return meat_f
