from akarpov.music.models import DownloadJob
from akarpov.music.services.download import detect_source
from akarpov.music.tasks import (
    process_dir_upload,
    process_download_job,
    process_file_upload,
)


def load_tracks(address: str, user_id: int, config_id: int = None):
    if address.startswith("/"):
        process_dir_upload.apply_async(kwargs={"path": address, "user_id": user_id})
        return

    from akarpov.users.models import User

    user = User.objects.get(id=user_id)
    job = DownloadJob.objects.create(
        url=address,
        source=detect_source(address),
        creator=user,
        config_id=config_id,
    )
    process_download_job.apply_async(kwargs={"job_id": job.id})


def load_track_file(file, user_id: int):
    process_file_upload.apply_async(kwargs={"path": file, "user_id": user_id})
