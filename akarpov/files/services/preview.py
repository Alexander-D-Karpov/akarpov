from math import ceil

import magic
from PIL import Image, ImageDraw, ImageFont
from preview_generator.manager import PreviewManager

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


def textfile_to_image(textfile_path) -> Image:
    """Convert text file to a grayscale image.

    arguments:
    textfile_path - the content of this file will be converted to an image
    font_path - path to a font file (for example impact.ttf)
    """
    # parse the file into lines stripped of whitespace on the right side
    with open(textfile_path) as f:
        lines = tuple(line.rstrip() for line in f.readlines())

    font: ImageFont = None
    large_font = 20  # get better resolution with larger size
    for font_filename in COMMON_MONO_FONT_FILENAMES:
        try:
            font = ImageFont.truetype(font_filename, size=large_font)
            print(f'Using font "{font_filename}".')
            break
        except OSError:
            print(f'Could not load font "{font_filename}".')
    if font is None:
        font = ImageFont.load_default()
        print("Using default font.")

    def _font_points_to_pixels(pt):
        return round(pt * 96.0 / 72)

    margin_pixels = 20

    # height of the background image
    tallest_line = max(lines, key=lambda line: font.getsize(line)[PIL_HEIGHT_INDEX])
    max_line_height = _font_points_to_pixels(
        font.getsize(tallest_line)[PIL_HEIGHT_INDEX]
    )
    realistic_line_height = max_line_height * 0.8
    image_height = int(ceil(realistic_line_height * len(lines) + 2 * margin_pixels))

    widest_line = max(lines, key=lambda s: font.getsize(s)[PIL_WIDTH_INDEX])
    max_line_width = _font_points_to_pixels(font.getsize(widest_line)[PIL_WIDTH_INDEX])
    image_width = int(ceil(max_line_width + (2 * margin_pixels)))

    # draw the background
    background_color = 255  # white
    image = Image.new(
        PIL_GRAYSCALE, (image_width, image_height), color=background_color
    )
    draw = ImageDraw.Draw(image)

    font_color = 0
    horizontal_position = margin_pixels
    for i, line in enumerate(lines):
        vertical_position = int(round(margin_pixels + (i * realistic_line_height)))
        draw.text(
            (horizontal_position, vertical_position), line, fill=font_color, font=font
        )

    return image


def create_preview(file_path: str) -> str:
    global manager
    # TODO: add text image generation/code image
    if not manager:
        manager = PreviewManager(cache_path, create_folder=True)
    if manager.has_jpeg_preview(file_path):
        return manager.get_jpeg_preview(file_path, height=500)
    return ""


def get_file_mimetype(file_path: str) -> str:
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)


def get_description(file_path: str) -> str:
    global manager
    if not manager:
        manager = PreviewManager(cache_path, create_folder=True)

    if manager.has_text_preview(file_path):
        return manager.get_text_preview(file_path)
    return ""


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
