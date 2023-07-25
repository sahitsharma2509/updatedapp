from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import Conversation,Knowledgebase


class TestChatPage(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.token = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token["access"]}')
        self.conversation = Conversation.objects.create(user=self.user, title='Test Conversation')
        self.knowledgebase = Knowledgebase.objects.create(user=self.user, name='Test Knowledgebase')

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_chat_page(self):
        response_conversation = self.client.get(reverse('conversations-list-create'))
        response_knowledgebases = self.client.get(reverse('get_knowledgebases'))
        
        self.assertEqual(response_conversation.status_code, status.HTTP_200_OK)
        self.assertEqual(response_knowledgebases.status_code, status.HTTP_200_OK)
        
        # Check that the conversation and knowledgebase exist in the response
        self.assertIsNotNone(response_conversation.data)
        self.assertIsNotNone(response_knowledgebases.data)
