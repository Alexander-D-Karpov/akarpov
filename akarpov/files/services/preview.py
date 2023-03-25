from math import ceil

from PIL import Image, ImageDraw, ImageFont
from preview_generator.manager import PreviewManager

cache_path = "/tmp/preview_cache"
PIL_GRAYSCALE = "L"
PIL_WIDTH_INDEX = 0
PIL_HEIGHT_INDEX = 1
COMMON_MONO_FONT_FILENAMES = [
    "DejaVuSansMono.ttf",
    "Consolas Mono.ttf",
    "Consola.ttf",
]


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
    # TODO: add text image generation/code image
    manager = PreviewManager(cache_path, create_folder=True)
    path_to_preview_image = manager.get_pdf_preview(file_path)
    return path_to_preview_image
