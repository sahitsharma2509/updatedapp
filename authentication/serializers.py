from rest_framework.serializers import ModelSerializer
from .models import Message,Conversation, PdfDocument
from django.contrib.auth.models import User
from rest_framework import serializers


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ('id', 'created_at', 'user')

class PdfDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfDocument
        fields = ('id', 'document', 'timestamp', 'user','name')

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'conversation', 'is_user', 'text', 'created_at')

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

    def to_representation(self, instance):
        print("UserSerializer.to_representation called")
        return super().to_representation(instance)
