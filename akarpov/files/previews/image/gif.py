from akarpov.files.models import File


def view(file: File):
    static = ""
    content = (
        f"""
    <div class="col-auto">
    <img class="img-fluid" src="{file.file.url}" rel:animated_src="{file.file.url}"
  rel:auto_play="1" rel:rubbable="1" />
  </div>
    """
        + r"""
    <script type="text/javascript" src="/static/js/jquery.min.js"></script>
    <script type="text/javascript" src="/static/js/libgif.js"></script>
    <script type="text/javascript">
    $('img').each(function (img_tag) {
        if (/.*\.gif/.test(img_tag.src)) {
            var rub = new SuperGif({ gif: img_tag } );
            rub.load(function(){
                console.log('oh hey, now the gif is loaded');
            });
        }
    });
    </script>
    """
    )

    return static, content
