from akarpov.files.models import File


def view(file: File) -> (str, str):
    static = (
        f"""
    <meta property="og:title" content="{file.name}" />
    """
        + """
    <style>
    #canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    }
    </style>
    """
    )
    content = (
        """
    <div id="container">
      <canvas id="canvas"></canvas>
      <audio id="audio"></audio>
    </div>
    """
        + """
    <script>
    const container = document.getElementById("container");
    container.addEventListener("click", function () {
      let audio1 = new Audio();
      """
        + f"""
      audio1.src = "{file.file.url}";
      """
        + """
      audio1.crossOrigin = "anonymous";
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)(); // for safari browser

      const container = document.getElementById("container");
      const canvas = document.getElementById("canvas");
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      const ctx = canvas.getContext("2d");

      let audioSource = null;
      let analyser = null;

      audio1.play();
      audioSource = audioCtx.createMediaElementSource(audio1);
      analyser = audioCtx.createAnalyser();
      audioSource.connect(analyser);
      analyser.connect(audioCtx.destination);
      analyser.fftSize = 128;
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const barWidth = canvas.width / 2 / bufferLength;

      let x = 0;

      function animate() {
        x = 0;
        ctx.clearRect(0, 0, canvas.width, canvas.height); // clears the canvas
        analyser.getByteFrequencyData(dataArray);
        drawVisualizer({ bufferLength, dataArray, barWidth });
        requestAnimationFrame(animate); // calls the animate function again. This method is built in
      }

      const drawVisualizer = ({ bufferLength, dataArray, barWidth }) => {
        let barHeight;
        for (let i = 0; i < bufferLength; i++) {
          barHeight = dataArray[i];
          const red = (i * barHeight) / 10;
          const green = i * 4;
          const blue = barHeight / 4 - 12;
          ctx.fillStyle = `rgb(${red}, ${green}, ${blue})`;
          ctx.fillRect(
            canvas.width / 2 - x, // this will start the bars at the center of the canvas and move from right to left
            canvas.height - barHeight,
            barWidth,
            barHeight
          );
          x += barWidth; // increases the x value by the width of the bar
        }

        for (let i = 0; i < bufferLength; i++) {
          barHeight = dataArray[i];
          const red = (i * barHeight) / 10;
          const green = i * 4;
          const blue = barHeight / 4 - 12;
          ctx.fillStyle = `rgb(${red}, ${green}, ${blue})`;
          ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
          x += barWidth; // increases the x value by the width of the bar
        }
      };

      animate();
    });

    </script>
    """
    )

    return static, content
