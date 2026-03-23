import json

from channels.db import database_sync_to_async
from django.utils.timezone import now

from akarpov.common.channels import BaseConsumer
from akarpov.music.api.serializers import SongSerializer
from akarpov.music.models import RadioSong
from akarpov.users.models import User


class RadioConsumer(BaseConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_group_name = None

    async def connect(self):
        self.room_group_name = "radio_main"
        await self.accept()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        data = await self.get_radio_song()
        if data:
            await self.send_json(data)

    @database_sync_to_async
    def get_radio_song(self):
        r = RadioSong.objects.filter(slug="")
        if r:
            r = r.first()
            return SongSerializer(context={"request": None}).to_representation(
                r.song
            ) | {"offset": (now() - r.start).seconds}
        return None

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except ValueError:
            await self.send_json(
                {"type": "ERROR", "message": "data is not JSON serializable"}
            )
            return
        return data

    async def song(self, event):
        data = event["data"]
        await self.send_json(data)


class DownloadProgressConsumer(BaseConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.group_name = "download_progress"

    async def connect(self):
        user_id = self.scope.get("user_id")
        if not user_id:
            await self.close()
            return

        is_super = await self._is_superuser(user_id)
        if not is_super:
            await self.close()
            return

        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    @database_sync_to_async
    def _is_superuser(self, user_id):
        try:
            return User.objects.get(id=user_id).is_superuser
        except User.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        pass

    async def download_update(self, event):
        await self.send_json(event["data"])
