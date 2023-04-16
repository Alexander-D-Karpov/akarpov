import string

from akarpov.files.models import File

text = " ".join(string.printable)
formats = {
    "ttf": "truetype",
    "otf": "opentype",
    "woff": "woff",
    "woff2": "woff2",
}


def view(file: File):
    name = file.file.path.split("/")[-1].split(".")[0]
    extension = file.file.path.split("/")[-1].split(".")[-1]
    static = (
        """
    <style>
    @font-face {
    """
        + f"""
        font-family: {name};
        src: url("{file.file.url}") format("{formats[extension]}");
        """
        + """
    }
    #text-example {
    """
        + f"""
      font-family: '{name}', serif;
      font-size: 48px;
    """
        + """
    }
    </style>
    """
    )
    content = f"""
    <div id="text-example" class="">
        {text}
    </div>
    """
    return static, content
