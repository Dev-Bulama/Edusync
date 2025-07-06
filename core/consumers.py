import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Meeting, MeetingParticipant
import uuid
from datetime import datetime

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.meeting_group_name = f'meeting_{self.meeting_id}'
        self.user = self.scope["user"]
        
        # Check if user can join meeting
        can_join = await self.check_meeting_permission()
        if not can_join:
            await self.close()
            return
        
        # Join meeting group
        await self.channel_layer.group_add(
            self.meeting_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.get_full_name(),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        # Notify others that user left
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'username': self.user.get_full_name(),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Leave meeting group
        await self.channel_layer.group_discard(
            self.meeting_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'webrtc_offer':
                await self.handle_webrtc_offer(data)
            elif message_type == 'webrtc_answer':
                await self.handle_webrtc_answer(data)
            elif message_type == 'webrtc_ice_candidate':
                await self.handle_ice_candidate(data)
            elif message_type == 'screen_share_start':
                await self.handle_screen_share_start(data)
            elif message_type == 'screen_share_stop':
                await self.handle_screen_share_stop(data)
            elif message_type == 'audio_toggle':
                await self.handle_audio_toggle(data)
            elif message_type == 'video_toggle':
                await self.handle_video_toggle(data)
            elif message_type == 'join_meeting':
                await self.handle_join_meeting(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON data'
            }))

    async def handle_chat_message(self, data):
        message = data.get('message', '').strip()
        if message:
            await self.channel_layer.group_send(
                self.meeting_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message': message,
                    'user_id': self.user.id,
                    'username': self.user.get_full_name(),
                    'timestamp': datetime.now().isoformat()
                }
            )

    async def handle_webrtc_offer(self, data):
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'webrtc_offer_broadcast',
                'offer': data.get('offer'),
                'from_user': self.user.id,
                'to_user': data.get('to_user'),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_webrtc_answer(self, data):
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'webrtc_answer_broadcast',
                'answer': data.get('answer'),
                'from_user': self.user.id,
                'to_user': data.get('to_user'),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_ice_candidate(self, data):
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'ice_candidate_broadcast',
                'candidate': data.get('candidate'),
                'from_user': self.user.id,
                'to_user': data.get('to_user'),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_screen_share_start(self, data):
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'screen_share_started',
                'user_id': self.user.id,
                'username': self.user.get_full_name(),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_screen_share_stop(self, data):
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'screen_share_stopped',
                'user_id': self.user.id,
                'username': self.user.get_full_name(),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_audio_toggle(self, data):
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'audio_toggled',
                'user_id': self.user.id,
                'username': self.user.get_full_name(),
                'muted': data.get('muted', False),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_video_toggle(self, data):
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'video_toggled',
                'user_id': self.user.id,
                'username': self.user.get_full_name(),
                'video_off': data.get('video_off', False),
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_join_meeting(self, data):
        # Mark attendance
        await self.mark_attendance()

    # Broadcast handlers
    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def chat_message_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def webrtc_offer_broadcast(self, event):
        if event['to_user'] == self.user.id or event['to_user'] == 'all':
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'offer': event['offer'],
                'from_user': event['from_user'],
                'timestamp': event['timestamp']
            }))

    async def webrtc_answer_broadcast(self, event):
        if event['to_user'] == self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_answer',
                'answer': event['answer'],
                'from_user': event['from_user'],
                'timestamp': event['timestamp']
            }))

    async def ice_candidate_broadcast(self, event):
        if event['to_user'] == self.user.id or event['to_user'] == 'all':
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'from_user': event['from_user'],
                'timestamp': event['timestamp']
            }))

    async def screen_share_started(self, event):
        await self.send(text_data=json.dumps({
            'type': 'screen_share_started',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def screen_share_stopped(self, event):
        await self.send(text_data=json.dumps({
            'type': 'screen_share_stopped',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def audio_toggled(self, event):
        await self.send(text_data=json.dumps({
            'type': 'audio_toggled',
            'user_id': event['user_id'],
            'username': event['username'],
            'muted': event['muted'],
            'timestamp': event['timestamp']
        }))

    async def video_toggled(self, event):
        await self.send(text_data=json.dumps({
            'type': 'video_toggled',
            'user_id': event['user_id'],
            'username': event['username'],
            'video_off': event['video_off'],
            'timestamp': event['timestamp']
        }))

    # Database operations
    @database_sync_to_async
    def check_meeting_permission(self):
        try:
            meeting = Meeting.objects.get(id=self.meeting_id)
            if meeting.organizer == self.user:
                return True
            if meeting.participants.filter(user=self.user, status='accepted').exists():
                return True
            if self.user.userprofile.user_type == 'admin':
                return True
            return False
        except Meeting.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_attendance(self):
        try:
            participant = MeetingParticipant.objects.get(
                meeting_id=self.meeting_id,
                user=self.user
            )
            participant.mark_attendance()
        except MeetingParticipant.DoesNotExist:
            pass