import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import JobApplication, JobPosting

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            self.room_group_name = f"notifications_{self.user.id}"
            
            logger.info(f"WebSocket connecting for user {self.user.username} (ID: {self.user.id})")
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"WebSocket connected for user {self.user.username}")
        else:
            logger.warning("WebSocket connection attempt by unauthenticated user")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            logger.info(f"WebSocket disconnecting for user {self.user.username}")
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        logger.info(f"Received message from user {self.user.username}: {message}")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'notification_message',
                'message': message
            }
        )

    async def notification_message(self, event):
        message = event['message']
        logger.info(f"Sending notification to user {self.user.username}: {message}")

        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def get_job_title(self, job_id):
        try:
            job = JobPosting.objects.get(id=job_id)
            return job.title
        except JobPosting.DoesNotExist:
            return "Unknown Job"

    @database_sync_to_async
    def get_application_status(self, application_id):
        try:
            application = JobApplication.objects.get(id=application_id)
            return application.status
        except JobApplication.DoesNotExist:
            return None 