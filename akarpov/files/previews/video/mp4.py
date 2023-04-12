from akarpov.files.models import File


def view(file: File) -> (str, str):
    static = """
    <link href="https://vjs.zencdn.net/8.0.4/video-js.css" rel="stylesheet" />
    """
    data = """"playbackRates": [0.5, 1, 1.5, 2], "responsive": true }"""
    content = f"""

      <video id="my_video_1" class="video-js vjs-default-skin" height="500px"
          controls poster='{file.preview.url if file.preview else ''}'
          data-setup='{data}'>
        <source src="{file.file.url}" type='video/mp4' />
      </video>

      <script src="https://vjs.zencdn.net/8.0.4/video.min.js"></script>
    """

    return static, content
