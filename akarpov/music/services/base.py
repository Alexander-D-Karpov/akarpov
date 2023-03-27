from akarpov.music.tasks import list_tracks, process_dir


def load_tracks(address: str):
    if address.startswith("/"):
        process_dir.apply_async(kwargs={"path": address})
    list_tracks.apply_async(kwargs={"url": address})


def load_track_file(file):
    ...
