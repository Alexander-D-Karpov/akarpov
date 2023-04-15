from . import application, audio, font, image, text, video

previews = {
    "application": {
        "zip": application.zip.view,
        "java-archive": application.zip.view,
        "doc": application.doc.view,
        "docx": application.docx.view,
        "vnd.oasis.opendocument.text": application.odt.view,
    },
    "audio": {
        "aac": audio.basic.view,
        "mpeg": audio.basic.view,
        "ogg": audio.oga.view,
        "opus": audio.basic.view,
        "wav": audio.basic.view,
        "webm": audio.basic.view,
    },
    "video": {
        "mp4": video.mp4.view,
        "ogg": video.basic.view,
        "mpeg": video.basic.view,
        "quicktime": video.basic.view,
    },
    "image": {
        "jpeg": image.basic.view,
        "png": image.basic.view,
        "avif": image.basic.view,
        "bmp": image.basic.view,
        "vnd.microsoft.icon": image.basic.view,
        "gif": image.gif.view,
    },
    "text": {
        "css": text.common.view,
        "html": text.common.view,
        "javascript": text.common.view,
        "plain": text.plain.view,
        "csv": text.csv.view,
    },
    "font": {"otf": font.otf.view},
}

source_code = {}
for ext in text.common.language_previews.keys():
    source_code[ext] = text.common.view

extensions = {
    "mp4": video.mp4.view,
    "mp3": audio.basic.view,
    "opus": audio.basic.view,
    "avif": image.basic.view,
    "bmp": image.basic.view,
    "jpeg": image.basic.view,
    "jpg": image.basic.view,
    "ico": image.basic.view,
    "mov": video.basic.view,
    "ogv": video.basic.view,
    "doc": application.doc.view,
    "docx": application.docx.view,
    "odt": application.odt.view,
    "gif": image.gif.view,
    "zip": application.zip.view,
    "jar": application.zip.view,
    "mpeg": video.mp4.view,
    "oga": audio.oga.view,
    "otf": font.otf.view,
} | source_code
