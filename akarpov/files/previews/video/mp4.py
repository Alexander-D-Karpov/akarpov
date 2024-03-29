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
