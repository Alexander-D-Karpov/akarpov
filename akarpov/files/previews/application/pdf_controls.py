from akarpov.files.models import File


def view(file: File):
    static = """
    <link href="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.4.120/web/pdf_viewer.min.css" rel="stylesheet">
    """

    content = (
        """
            <header>
            <div class="col-auto">
            <ul class="navigation">
                <li class="navigation__item">
                    <!-- Navigate to the Previous and Next pages -->
                    <a href="#" class="previous round" id="prev_page">
                        <i class="fas fa-arrow-left"></i>
                    </a>

                    <!-- Navigate to a specific page -->
                    <input type="number" value="1" id="current_page" />

                    <a href="#" class="next round" id="next_page">
                        <i class="fas fa-arrow-right"></i>
                    </a>

                    <!-- Page Info -->
                    Page
                    <span id="page_num"></span>
                    of
                    <span id="page_count"></span>
                </li>

                <!-- Zoom In and Out -->
                <li class="navigation__item">
                    <button class="zoom" id="zoom_in">
                        <i class="fas fa-search-plus"></i>
                    </button>

                    <button class="zoom" id="zoom_out">
                        <i class="fas fa-search-minus"></i>
                    </button>
                </li>
            </ul>
        </header>

        <!-- Canvas to place the PDF -->
        <canvas id="canvas" class="canvas__container w-50"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.4.120/build/pdf.min.js"></script>
        <script>
        """
        + f"""
        const pdf = '{file.file.url}';
        """
        + """
        const pageNum = document.querySelector('#page_num');
        const pageCount = document.querySelector('#page_count');
        const currentPage = document.querySelector('#current_page');
        const previousPage = document.querySelector('#prev_page');
        const nextPage = document.querySelector('#next_page');
        const zoomIn = document.querySelector('#zoom_in');
        const zoomOut = document.querySelector('#zoom_out');

        const initialState = {
            pdfDoc: null,
            currentPage: 1,
            pageCount: 0,
            zoom: 1,
        };
        pdfjsLib
        .getDocument(pdf)
        .promise.then((data) => {
            initialState.pdfDoc = data;
            console.log('pdfDocument', initialState.pdfDoc);

            pageCount.textContent = initialState.pdfDoc.numPages;

            renderPage();
        })
        .catch((err) => {
            alert(err.message);
        });

        const renderPage = () => {
        // Load the first page.
        console.log(initialState.pdfDoc, 'pdfDoc');
        initialState.pdfDoc
            .getPage(initialState.currentPage)
            .then((page) => {
                console.log('page', page);

                const canvas = document.querySelector('#canvas');
                const ctx = canvas.getContext('2d');
                const viewport = page.getViewport({
                    scale: initialState.zoom,
                });

                canvas.height = viewport.height;
                canvas.width = viewport.width;

                // Render the PDF page into the canvas context.
                const renderCtx = {
                    canvasContext: ctx,
                    viewport: viewport,
                };

                page.render(renderCtx);

                pageNum.textContent = initialState.currentPage;
            });
    };
    const showPrevPage = () => {
        if (initialState.pdfDoc === null || initialState.currentPage <= 1)
            return;
        initialState.currentPage--;
        // Render the current page.
        currentPage.value = initialState.currentPage;
        renderPage();
    };

    const showNextPage = () => {
        if (
            initialState.pdfDoc === null ||
            initialState.currentPage >= initialState.pdfDoc._pdfInfo.numPages
        )
            return;

        initialState.currentPage++;
        currentPage.value = initialState.currentPage;
        renderPage();
    };

    // Button events.
    previousPage.addEventListener('click', showPrevPage);
    nextPage.addEventListener('click', showNextPage);
    currentPage.addEventListener('keypress', (event) => {
        if (initialState.pdfDoc === null) return;
        // Get the key code.
        const keycode = event.keyCode ? event.keyCode : event.which;

        if (keycode === 13) {
            // Get the new page number and render it.
            let desiredPage = currentPage.valueAsNumber;
            initialState.currentPage = Math.min(
                Math.max(desiredPage, 1),
                initialState.pdfDoc._pdfInfo.numPages,
            );

            currentPage.value = initialState.currentPage;
            renderPage();
        }
    });
    zoomIn.addEventListener('click', () => {
        if (initialState.pdfDoc === null) return;
        initialState.zoom *= 4 / 3;
        renderPage();
    });

    zoomOut.addEventListener('click', () => {
        if (initialState.pdfDoc === null) return;
        initialState.zoom *= 2 / 3;
        renderPage();
    });
    </script>
    """
    )

    return static, content
