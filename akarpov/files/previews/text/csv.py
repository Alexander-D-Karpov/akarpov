import csv

import chardet
import structlog

from akarpov.files.models import File

logger = structlog.get_logger(__name__)


def view(file: File):
    try:
        try:
            with open(file.file.path, newline="") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                for row in reader:
                    print(row)
        except UnicodeDecodeError:
            rawdata = open("file.csv", "rb").read()
            enc = chardet.detect(rawdata)
            print(enc)
            with open(file.file.path, newline="", encoding=enc["encoding"]) as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                for row in reader:
                    print(row)
    except Exception as e:
        logger.error(e)
    static = ""
    content = ""
    return static, content
