from . import application, audio, image, text, video

previews = {
    "application": {
        "zip": application.zip.view,
    },
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
        "bmp": image.basic.view,
    },
    "text": {"css": text.common.view, "plain": text.plain.view},
}

source_code = {}
for ext in text.common.language_previews.keys():
    source_code[ext] = text.common.view

extensions = {
    "mp4": video.mp4.view,
    "mp3": audio.basic.view,
    "avif": image.basic.view,
    "bmp": image.basic.view,
    "mov": video.basic.view,
} | source_code
