import chardet
import textract
from textract.exceptions import ExtensionNotSupported


def extract_file_text(file: str) -> str:
    try:
        text = textract.process(file)
    except ExtensionNotSupported:
        try:
            rawdata = open(file, "rb").read()
            enc = chardet.detect(rawdata)
            with open(file, encoding=enc["encoding"]) as f:
                text = f.read()
        except Exception:
            return ""

    return text
