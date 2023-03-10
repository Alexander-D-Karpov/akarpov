import gzip
import mimetypes
import shutil
from contextlib import closing

from django.utils.encoding import force_bytes
from django_s3_storage.storage import (
    _UNCOMPRESSED_SIZE_META_KEY,
    S3Storage,
    _wrap_errors,
)


class FixedS3Storage(S3Storage):
    """
    Стандартный S3Storage использует boto3 для загрузки файла, который закрывает переданный
    content-файл. Однако imagekit должен повторно его использовать, поэтому нужно обернуть
    переданный контент во временный файл.
    """

    @_wrap_errors
    def _save(self, name, content):
        put_params = self._object_put_params(name)
        temp_files = []
        # The Django file storage API always rewinds the file before saving,
        # therefor so should we.
        content.seek(0)
        # Convert content to bytes.
        temp_file = self.new_temporary_file()
        temp_files.append(temp_file)
        for chunk in content.chunks():
            temp_file.write(force_bytes(chunk))
        temp_file.seek(0)
        content = temp_file
        # Calculate the content type.
        content_type, _ = mimetypes.guess_type(name, strict=False)
        content_type = content_type or "application/octet-stream"
        put_params["ContentType"] = content_type
        # Calculate the content encoding.
        if self.settings.AWS_S3_GZIP:
            # Check if the content type is compressible.
            content_type_family, content_type_subtype = content_type.lower().split("/")
            content_type_subtype = content_type_subtype.split("+")[-1]
            if content_type_family == "text" or content_type_subtype in (
                "xml",
                "json",
                "html",
                "javascript",
            ):
                # Compress the content.
                temp_file = self.new_temporary_file()
                temp_files.append(temp_file)
                with closing(gzip.GzipFile(name, "wb", 9, temp_file)) as gzip_file:
                    shutil.copyfileobj(content, gzip_file)
                # Only use the compressed version if the zipped version is actually smaller!
                orig_size = content.tell()
                if temp_file.tell() < orig_size:
                    temp_file.seek(0)
                    content = temp_file
                    put_params["ContentEncoding"] = "gzip"
                    put_params["Metadata"][_UNCOMPRESSED_SIZE_META_KEY] = "{:d}".format(
                        orig_size
                    )
                else:
                    content.seek(0)
        # Save the file.
        self.s3_connection.upload_fileobj(
            content,
            put_params.pop("Bucket"),
            put_params.pop("Key"),
            ExtraArgs=put_params,
            Config=self._transfer_config,
        )
        # Close all temp files.
        for temp_file in temp_files:
            temp_file.close()
        # All done!
        return name
