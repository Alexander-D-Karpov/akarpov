import string

from akarpov.files.models import File


def view(file: File):
    text = " ".join(string.printable)
    name = file.file.path.split("/")[-1].split(".")[0]
    static = (
        """
    <style>
    @font-face {
    """
        + f"""
        font-family: {name};
        src: url("{file.file.url}") format("opentype");
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
