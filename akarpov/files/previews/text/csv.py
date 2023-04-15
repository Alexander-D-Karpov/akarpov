import csv

import chardet
import structlog

from akarpov.files.models import File

logger = structlog.get_logger(__name__)


def get_csv_table(reader):
    content = "<div class='col-auto'><table class='table table-hover'>"
    header = next(reader)
    content += """<thead><tr>"""
    for el in header:
        content += f"""<th scope="col">{el}</th>"""
    content += """</tr></thead>\n"""
    if header:
        content += """<tbody>"""
        i = 0
        for row in reader:
            r = "<tr>"
            if i >= 5000:
                for _ in header:
                    r += """<th>the remaining data was trunked</th>"""
                r += "</tr>\n"
                content += r
                break
            for ind, el in enumerate(row):
                if ind == 0:
                    r += f"""<th scope="row">{el}</th>"""
                else:
                    r += f"""<th>{el}</th>"""
            r += "</tr>\n"
            content += r
            i += 1
        content += """</tbody>"""
    content += "</table></div>"
    return content


def view(file: File):
    try:
        try:
            with open(file.file.path, newline="") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                content = get_csv_table(reader)
        except UnicodeDecodeError:
            rawdata = open(file.file.path, "rb").read()
            enc = chardet.detect(rawdata)
            with open(file.file.path, newline="", encoding=enc["encoding"]) as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                content = get_csv_table(reader)
    except Exception as e:
        content = "couldn't parse csv file"
        logger.error(e)
    static = ""
    return static, content
