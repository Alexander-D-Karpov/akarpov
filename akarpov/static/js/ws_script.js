// Determine the correct WebSocket protocol to use
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host; // Assuming host includes the port if needed
const socketPath = `${protocol}//${host}/ws/radio/`;

let socket = new WebSocket(socketPath);

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Your existing timeSince function can remain unchanged

// Update the onmessage handler here as needed for the music player
socket.onmessage = function(event) {
    let data = JSON.parse(event.data);
    // Process the data
};

// This function will attempt to reconnect the WebSocket after a 5-second delay
async function reconnectSocket() {
    console.log("Radio socket disconnected, reconnecting...");
    let socketClosed = true;
    await sleep(5000); // Wait 5 seconds before attempting to reconnect
    while (socketClosed) {
        try {
            socket = new WebSocket(socketPath);
            socket.onmessage = onMessageHandler; // Reassign your onmessage handler
            socket.onclose = onSocketCloseHandler; // Reassign the onclose handler to this function
            socketClosed = false; // Exit the loop if the connection is successful
        } catch (e) {
            console.log("Can't connect to socket, retrying in 1 second...");
            await sleep(1000); // Wait 1 second before retrying
        }
    }
}

// Define a separate function for the onclose event
const onSocketCloseHandler = async function(event) {
    if (!event.wasClean) {
        // Only attempt to reconnect if the socket did not close cleanly
        await reconnectSocket();
    }
};

// Assign the onclose handler to the socket
socket.onclose = onSocketCloseHandler;
let isAdmin = false; // This will be set based on socket connect data for admin TODO: retrieve from server



function displaySong(data) {
  // Display song details using jQuery to manipulate the DOM
  $('#song-info').html(/* HTML structure for song info */);
  // Update admin controls if isAdmin is true
  if (isAdmin) {
    $('#admin-controls').show();
    // Add slider and other controls
  }
  // Add song to history
  addToHistory(data);
}

function displayAdminControls(data) {
  // Display admin controls if user is admin
  if (isAdmin) {
    $('#admin-controls').html(/* HTML structure for admin controls */);
  }
}

function updateSong(data) {
  // Update the song information on the page
  displaySong(data);
}

function addToHistory(songData) {
  var authors = songData.authors.map(author => author.name).join(", ");
  var historyItemHtml = `
    <div class="card mb-3" style="max-width: 540px;">
        <div class="row g-0">
            <div class="col-md-4">
                <img src="${songData.image}" class="img-fluid rounded-start" alt="${songData.name}">
            </div>
            <div class="col-md-8">
                <div class="card-body">
                    <h5 class="card-title">${songData.name}</h5>
                    <p class="card-text"><small class="text-muted">by ${authors}</small></p>
                    <p class="card-text">${songData.album.name}</p>
                    <!-- Admin controls would go here if needed -->
                </div>
            </div>
        </div>
    </div>
  `;
  $('#history').prepend(historyItemHtml); // prepend to add it to the top of the list
}

// Functionality to handle sliding track length and selecting track to play
// ...

// ws_script.js

$(document).ready(function() {
    var audioContext;
    var analyser;
    var started = false; // Flag to indicate if the audio context has started
    var audio = document.getElementById('audio-player');
    var canvas = document.getElementById('audio-visualization');
    var ctx = canvas.getContext('2d');

    // Function to initialize the AudioContext and analyser
    function initAudioContext() {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        var audioSrc = audioContext.createMediaElementSource(audio);
        audioSrc.connect(analyser);
        analyser.connect(audioContext.destination);
    }

    // Function to start or resume the audio context on user interaction
    function startOrResumeContext() {
        if (audioContext.state === 'suspended') {
            audioContext.resume().then(() => {
                console.log('Playback resumed successfully');
            });
        }
    }

    // Volume control listener
    $('#volume-control').on('input change', function() {
        if (audio) {
            audio.volume = $(this).val() / 100;
        }
    });

    // Listener for play/pause button
    $('#play-pause-button').on('click', function() {
        if (!started) {
            initAudioContext();
            started = true;
        }

        startOrResumeContext(); // Resume the audio context if needed

        if (audio.paused) {
            audio.play().then(() => {
                console.log('Audio playing');
            }).catch((e) => {
                console.error('Error playing audio:', e);
            });
        } else {
            audio.pause();
            console.log('Audio paused');
        }
    });

    function renderFrame() {
        if (!analyser) return;

        requestAnimationFrame(renderFrame);
        var fbc_array = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(fbc_array);
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
        // Visualization code...
    }

    // Error event listener for the audio element
    audio.addEventListener('error', function(e) {
        console.error('Error with audio playback:', e);
    });

    // Attempt to play the audio and start visualization when the audio can play through
    audio.addEventListener('canplaythrough', function() {
        startOrResumeContext();
        renderFrame(); // Start the visualizer
    });
});
