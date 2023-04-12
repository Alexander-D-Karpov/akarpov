from akarpov.files.models import File


def view(file: File) -> (str, str):
    static = f"""
    <link  href="https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.11.3/viewer.min.css" rel="stylesheet">
    <meta property="og:title" content="{file.name}" />
    """
    content = (
        f"""
        <div>
          <img id="image" class="img-fluid" src="{file.file.url}" alt="Picture">
        </div>
        <div id="images">
        </div
      <script src="/static/js/jquery.js"></script>
    """
        + """
          <script src="https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.11.3/viewer.min.js">
            var $image = $('#image');

            $image.viewer({
              inline: true,
              viewed: function() {
                $image.viewer('zoomTo', 1);
              }
            });

            var viewer = $image.data('viewer');
            $('#images').viewer();
      </script>
    """
    )

    return static, content
