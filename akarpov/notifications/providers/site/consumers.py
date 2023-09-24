from akarpov.common.channels import BaseConsumer


class NotificationsConsumer(BaseConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_group_name = None

    async def connect(self):
        self.room_group_name = f"notifications_{self.scope['user_id']}"

        await self.accept()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        if not self.scope["user_id"]:
            await self.send_error("Authorization is required")
            await self.disconnect(close_code=None)
            return

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.close()

    async def receive_json(self, content: dict, **kwargs):
        return content

    async def notification(self, event):
        data = event["data"]
        await self.send_json(data)
