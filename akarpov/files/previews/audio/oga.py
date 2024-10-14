from akarpov.files.models import File


def view(file: File) -> (str, str):
    static = f"""
    <meta property="og:title" content="{file.name}" />
    """
    text = file.content.replace("\t", "    ")
    content = (
        """
    <div id="waveform">
    </div>
    <div id="wave-timeline"> </div>

    <div class="controls mt-4 d-flex align-items-center justify-content-center text-center">
        <button class="btn btn-primary" data-action="play">
            <i class="glyphicon glyphicon-play"></i>
            Play
            /
            <i class="glyphicon glyphicon-pause"></i>
            Pause
        </button>
    </div>"""
        + f"""
    <div>{text}</div>
    """
        + """
    <script src="https://unpkg.com/wavesurfer.js@6.6.3/dist/wavesurfer.js"></script>
    <script src="https://unpkg.com/wavesurfer.js@6.6.3/dist/plugin/wavesurfer.timeline.min.js"></script>
    <script src="https://unpkg.com/wavesurfer.js@6.6.3/dist/plugin/wavesurfer.regions.min.js"></script>
    <script>
    window.onload = function() {
    wavesurfer = WaveSurfer.create({
        container: document.querySelector('#waveform'),
        waveColor: '#D9DCFF',
        progressColor: '#4353FF',
        cursorColor: '#4353FF',
        barWidth: 3,
        barRadius: 3,
        cursorWidth: 1,
        height: 200,
        barGap: 3,
        plugins: [
            WaveSurfer.regions.create({}),
            WaveSurfer.timeline.create({
                container: "#wave-timeline"
            })
        ]
    });

    wavesurfer.on('error', function(e) {
        console.warn(e);
    });
    """
        + f"""
    wavesurfer.load('{file.file.url}');
    """
        + """
    document
        .querySelector('[data-action="play"]')
        .addEventListener('click', wavesurfer.playPause.bind(wavesurfer));
    }
    </script>
    """
    )

    return static, content
