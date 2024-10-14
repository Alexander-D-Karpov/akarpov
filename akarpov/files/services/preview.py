import magic

from akarpov.files.models import File

cache_path = "/tmp/preview_cache"
PIL_GRAYSCALE = "L"
PIL_WIDTH_INDEX = 0
PIL_HEIGHT_INDEX = 1
COMMON_MONO_FONT_FILENAMES = [
    "DejaVuSansMono.ttf",
    "Consolas Mono.ttf",
    "Consola.ttf",
]

manager = None


def get_file_mimetype(file_path: str) -> str:
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)


def get_base_meta(file: File):
    preview = file.preview.url if file.preview else ""
    description = file.description if file.description else ""
    return f"""
    <meta property="og:type" content="website">
    <meta property="og:title" content="{file.name}">
    <meta property="og:url" content="{file.get_absolute_url()}">
    <meta property="og:image" content="{preview}">
    <meta property="og:image:width" content="500" />
    <meta property="og:image:height" content="500" />
    <meta property="og:description" content="{description}">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{file.name}">
    <meta name="twitter:site" content="{file.get_absolute_url()}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{preview}">
    <meta property="twitter:image:width" content="500" />
    <meta property="twitter:image:height" content="500" />
    <meta name="twitter:image:alt" content="{file.name}">
    """
