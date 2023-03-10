from upload_validator import FileTypeValidator

validate_excel = FileTypeValidator(
    allowed_types=[
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    ],
    allowed_extensions=[".xlsx"],
)

validate_zip = FileTypeValidator(
    allowed_types=[
        "application/zip",
        "application/octet-stream",
        "application/x-zip-compressed",
        "multipart/x-zip",
    ],
    allowed_extensions=[".zip"],
)
