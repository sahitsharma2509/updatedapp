from rest_framework.serializers import ModelSerializer
from .models import Message,Conversation,  Knowledgebase, KnowledgeDocument,UserProfile
from django.contrib.auth.models import User
from rest_framework import serializers



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

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Make 'user' field read-only
    token_limit = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('user', 'avatar', 'tokens_used', 'token_limit', 'tokens_remaining')

    def get_token_limit(self, obj):
        if obj.plan:
            return obj.plan.token_limit
        return None



from rest_framework import serializers
from .models import Knowledgebase





class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = ['id', 'document_type', 'data', 'content']


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