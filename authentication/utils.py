from rest_framework.response import Response
from .models import Message,UserProfile
from .serializers import MessageSerializer
from django.apps import apps

from django.utils import timezone


def getMessage(request, conversation_id):
    Message = apps.get_model('authentication', 'Message')
    chat = Message.objects.filter(conversation=conversation_id).order_by('created_at')
    serializer = MessageSerializer(chat, many=True)
    return Response(serializer.data)



