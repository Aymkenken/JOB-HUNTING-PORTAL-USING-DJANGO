import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Job, JobApplication

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            if self.scope["user"].is_authenticated:
                self.user = self.scope["user"]
                self.room_group_name = f"notifications_{self.user.id}"
                
                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                
                await self.accept()
                print(f"WebSocket connected for user {self.user.id}")
            else:
                print("Unauthenticated connection attempt")
                await self.close()
        except Exception as e:
            print(f"Error in connect: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                # Leave room group
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                print(f"WebSocket disconnected for user {self.user.id}")
        except Exception as e:
            print(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'notification_message',
                    'message': message
                }
            )
        except Exception as e:
            print(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to process message'
            }))

    async def notification_message(self, event):
        try:
            message = event['message']
            
            # Add timestamp to the message
            if isinstance(message, dict):
                message['timestamp'] = self.get_timestamp()
            
            # Send message to WebSocket
            await self.send(text_data=json.dumps(message))
            print(f"Notification sent to user {self.user.id}: {message}")
        except Exception as e:
            print(f"Error in notification_message: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to send notification'
            }))
    
    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S") 