import os

from django.core.files import File

from akarpov.music.models import Album, Author, MusicDraft, Song


def save_song_from_draft(draft: MusicDraft) -> Song | None:
    """
    Create a Song instance from a completed MusicDraft
    """
    try:
        if not draft.files.exists():
            draft.status = "failed"
            draft.error_message = "No files associated with draft"
            draft.save()
            return None

        # Get the music file
        draft_file = draft.files.filter(mime_type__startswith="audio/").first()
        if not draft_file:
            draft.status = "failed"
            draft.error_message = "No audio file found in draft"
            draft.save()
            return None

        # Get metadata from draft
        meta_data = draft.meta_data or {}

        # Create song instance
        song = Song(
            name=meta_data.get("title", ""),
            length=meta_data.get("length"),
            link=draft.original_url,
            meta=meta_data,
        )

        # Handle album
        if "album" in meta_data:
            album, _ = Album.objects.get_or_create(
                name=meta_data["album"].get("name", ""),
                defaults={"meta": meta_data["album"]},
            )
            song.album = album

        # Save song to get an ID
        with open(draft_file.file.path, "rb") as f:
            song.file.save(
                os.path.basename(draft_file.original_name), File(f), save=True
            )

        # Handle authors
        if "artists" in meta_data:
            authors = []
            for artist_data in meta_data["artists"]:
                author, _ = Author.objects.get_or_create(
                    name=artist_data.get("name", ""), defaults={"meta": artist_data}
                )
                authors.append(author)
            song.authors.set(authors)

        # Handle image if present
        image_file = draft.files.filter(mime_type__startswith="image/").first()
        if image_file:
            with open(image_file.file.path, "rb") as f:
                song.image.save(
                    os.path.basename(image_file.original_name), File(f), save=True
                )

        # Add user if specified
        if draft.user_id:
            song.creator_id = draft.user_id
            song.save()

        # Clean up draft files
        draft.delete()

        return song

    except Exception as e:
        draft.status = "failed"
        draft.error_message = str(e)
        draft.save()
        return None
