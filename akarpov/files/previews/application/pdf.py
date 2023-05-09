from akarpov.files.models import File


def view(file: File):
    static = """
    <style>
      #pdf-viewer {
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.1);
        overflow: auto;
      }

      .pdf-page-canvas {
        display: block;
        margin: 5px auto;
        border: 1px solid rgba(0, 0, 0, 0.2);
      }
    </style>

    """

    content = (
        f"""
        <a href="{file.file.url}">View in system pdf viewer</a>"""
        + """
        <div id="pdf" class="col-auto">
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.5.141/pdf.min.js"></script>
        <script>
        """
        + f"""
        const url = '{file.file.url}';
        """
        + """
        var currPage = 1;
        var numPages = 0;
        var thePDF = null;
          pdfjsLib.GlobalWorkerOptions.workerSrc =
'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.5.141/pdf.worker.min.js';
  const loadingTask = pdfjsLib.getDocument(url);
  (async () => {
    const pdf = await loadingTask.promise;
    thePDF = pdf;
    numPages = pdf.numPages;
    await handlePages(1);

    async function handlePages(curr) {
        const scale = 1.5;
        const page = await pdf.getPage(curr);
        const viewport = page.getViewport({ scale });
        // Support HiDPI-screens.
        const outputScale = window.devicePixelRatio || 1;

        var canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");

        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = Math.floor(viewport.width) + "px";
        canvas.style.height = Math.floor(viewport.height) + "px";

        const transform = outputScale !== 1
          ? [outputScale, 0, 0, outputScale, 0, 0]
          : null;

        const renderContext = {
          canvasContext: context,
          transform,
          viewport,
        };
        page.render(renderContext);
        document.getElementById("pdf").appendChild(canvas);

        curr++;
        if (thePDF !== null && curr <= numPages) {
            await handlePages(curr+1);
        }
    }
  })();
</script>

        """
    )

    return static, content
