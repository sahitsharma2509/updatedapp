from rest_framework.serializers import ModelSerializer
from .models import Message,Conversation, PdfDocument, YouTubeLink, Knowledgebase, KnowledgeDocument
from django.contrib.auth.models import User
from rest_framework import serializers





class PdfDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfDocument
        fields = ('id', 'document', 'timestamp', 'user','name')

class YouTubeLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = YouTubeLink
        fields = ('id', 'url', 'timestamp', 'user')

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


from rest_framework import serializers
from .models import Knowledgebase



class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = ['id', 'document_type', 'data']


class KnowledgebaseSerializer(serializers.ModelSerializer):
    documents = KnowledgeDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Knowledgebase
        fields = ['id', 'name', 'user', 'documents','timestamp']


class ConversationSerializer(serializers.ModelSerializer):
    knowledge_base = KnowledgebaseSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'knowledge_base', 'created_at', 'title', 'document_types']