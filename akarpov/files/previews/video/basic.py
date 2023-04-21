import ffmpeg

from akarpov.files.models import File


def view(file: File) -> (str, str):
    static = f"""
    <meta property="og:title" content="{file.name}" />
    <meta property="og:type" content="video.movie" />
    <meta property="og:video" content="{file.file.url}" />
    <meta property="og:video:type" content="{file.file_type}" />
    <meta property="og:video:width" content="720" />
    <meta property="og:video:height" content="480" />
    <link href="https://vjs.zencdn.net/8.0.4/video-js.css" rel="stylesheet" />
    """
    data = """{"playbackRates": [0.5, 1, 1.5, 2], fit: true }"""
    content = f"""

    <div class="col-auto d-flex">
      <video id="video" class="video-js vjs-default-skin"
          controls poster='{file.preview.url if file.preview else ''}'
          preload="auto"
          data-setup='{data}'>
        <source src="{file.file.url}" type='{file.file_type}' />
      </video>
    </div>
      <script src="https://vjs.zencdn.net/8.0.4/video.min.js"></script>
    """

    return static, content


def meta(file: File):
    stream = ffmpeg.probe(file.file.path, select_streams="v")["streams"][0]
    width = ""
    height = ""
    preview = file.preview.url if file.preview else ""
    url = file.get_absolute_url()
    description = file.description if file.description else ""
    if "width" in stream:
        width = stream["width"]
    if "height" in stream:
        height = stream["height"]

    meat_f = f"""
    <meta property="og:site_name" content="akarpov">
    <meta property="og:url" content="{url}">
    <meta property="og:title" content="{file.name}">
    <meta property="og:image" content="{preview}">

    <meta property="og:description" content="{description}">

    <meta property="og:type" content="video">
    <meta property="og:video:url" content="{file.file.url}">
    <meta property="og:video:secure_url" content="{file.file.url}">
    <meta property="og:video:type" content="{file.file_type}">
    <meta property="og:video:width" content="1280">
    <meta property="og:video:height" content="720">
    <meta property="og:video:url" content="{file.file.url}">
    <meta property="og:video:secure_url" content="{file.file.url}">
    <meta property="og:video:type" content="{file.file_type}">
    <meta property="og:video:width" content="{width}">
    <meta property="og:video:height" content="{height}">

    <meta name="twitter:card" content="player">
    <meta name="twitter:site" content="{url}">
    <meta name="twitter:url" content="{url}">
    <meta name="twitter:title" content="{file.name}">
    <meta name="twitter:description" content="{file.description}">
    <meta name="twitter:image" content="{preview}">
    <meta name="twitter:app:name:iphone" content="Akarpov">
    <meta name="twitter:app:name:ipad" content="Akarpov">
    <meta name="twitter:app:name:googleplay" content="Akarpov">
    <meta name="twitter:player" content="{file.file.url}">
    <meta name="twitter:player:width" content="{width}">
    <meta name="twitter:player:height" content="{height}">
    """
    return meat_f
