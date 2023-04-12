from . import audio, image, video

previews = {
    "audio": {
        "aac": audio.basic.view,
        "mpeg": audio.basic.view,
        "ogg": audio.basic.view,
        "opus": audio.basic.view,
        "wav": audio.basic.view,
        "webm": audio.basic.view,
    },
    "video": {"mp4": video.mp4.view, "quicktime": video.basic.view},
    "image": {
        "jpeg": image.basic.view,
        "png": image.basic.view,
        "avif": image.basic.view,
    },
}

extensions = {
    "mp4": video.mp4.view,
    "mp3": audio.basic.view,
    "avif": image.basic.view,
    "mov": video.basic.view,
}
