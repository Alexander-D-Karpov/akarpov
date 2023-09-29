from akarpov.music.tasks import list_tracks, process_dir, process_file


def load_tracks(address: str, user_id: int):
    if address.startswith("/"):
        process_dir.apply_async(kwargs={"path": address, "user_id": user_id})
    list_tracks.apply_async(kwargs={"url": address, "user_id": user_id})


def load_track_file(file, user_id: int):
    process_file.apply_async(kwargs={"path": file, "user_id": user_id})
