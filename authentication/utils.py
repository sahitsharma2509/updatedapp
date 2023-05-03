from rest_framework.response import Response
from .models import Message
from .serializers import MessageSerializer


def getMessage(request, conversation_id):
    chat = Message.objects.filter(conversation=conversation_id).order_by('created_at')
    serializer = MessageSerializer(chat, many=True)
    return Response(serializer.data)
