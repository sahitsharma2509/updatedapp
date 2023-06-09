import json
from .loaders import readFile,get_response
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.cache import cache
from .models import Conversation, Vectorstore, Message, Knowledgebase
import json
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import jwt
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from .loaders import get_response


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = 'chat_%s' % self.room_name

        # Get the token
        token = self.scope['query_string'].decode('utf-8')
        token = token.split('=')[1]


        # Try to authenticate the user
        try:
            # Validate the token
            token_obj = AccessToken(token)


            # Get the user
            self.user = await self.get_user(token_obj['user_id'])


            if self.user is not None:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
            else:
                raise ValueError("Invalid user")
        except (InvalidToken, TokenError, ValueError) as e:
            print(f"Error: {e}")  # Debugging line
            print("Connection rejected, user not authenticated")  # Debugging line
            await self.close()

    @database_sync_to_async
    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        # Leave room group
        print(f"Disconnecting from {self.room_group_name}")  # Debugging line
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def get_conversation(self,conversation_id):
        return Conversation.objects.get(pk=conversation_id)

    @database_sync_to_async
    def create_message(self,conversation, is_user, text):
        return Message.objects.create(conversation=conversation, is_user=is_user, text=text)
    
    @database_sync_to_async
    def get_knowledge_base(self, conversation):
        return conversation.knowledge_base
    @database_sync_to_async
    def get_vectorstore(self, user_id, knowledgebase_id):
        try:
            vectorstore = Vectorstore.objects.filter(user=user_id, knowledgebase_id=knowledgebase_id).first()
            return vectorstore
        except Vectorstore.DoesNotExist:
        # Handle the case where the Vectorstore does not exist
            return None

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        conversation_id = text_data_json['conversation']
        is_user = text_data_json['is_user']
        text = text_data_json['text']

        print(f"Received message: {text} from user: {is_user}")  # Add this line

    # Get the conversation
        conversation = await self.get_conversation(conversation_id)

    # Get the knowledgebase
        knowledgebase = await self.get_knowledge_base(conversation)


        if knowledgebase is not None:
            print(f"Working with Knowledgebase link: {knowledgebase.name}")

    # Get the cache key and value
        cache_key = f'pinecone_index_v2:{self.user.id}:{knowledgebase.id}'
        cache_value = cache.get(cache_key)
        pinecone_index = cache_value.get('index', None) if cache_value else None
        namespace = cache_value.get('namespace', None) if cache_value else None

    # If pinecone_index is None, get the vectorstore
        if pinecone_index is None:
            vectorstore = await self.get_vectorstore(self.user.id, knowledgebase.id)
            pinecone_index = vectorstore.index
            namespace = vectorstore.namespace
            cache.set(cache_key, {'index': pinecone_index, 'namespace': namespace})

    # Get the response
        response = await get_response(text, str(pinecone_index), namespace)

        # Get the response

 

    # Create the messages
        message_user = await self.create_message(conversation, True, text)
        message_bot = await self.create_message(conversation, False, response)

        await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "chat.message",
            "message": response,
            "username": self.user.username,
            "is_user": False,
        },
    )
    
    
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
