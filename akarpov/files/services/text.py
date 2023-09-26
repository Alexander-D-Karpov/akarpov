import textract


def extract_file_text(file: str) -> str:
    text = textract.process(file)

    return text
