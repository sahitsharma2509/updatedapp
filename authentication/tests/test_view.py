from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import Conversation 
from django.test import TestCase

class TestViews(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.token = self.get_tokens_for_user(self.user)
        self.api_authentication()

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token['access'])

    def test_get_knowledgebases(self):
        response = self.client.get(reverse('get_knowledgebases'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)



class TestConversationViews(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.token = self.get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token['access'])


    # Create a sample conversation for testing the list view
        self.conversation = Conversation.objects.create(user=self.user, title="Sample Conversation")



    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def test_conversation_list(self):
        response = self.client.get(reverse('conversations-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Since we created one conversation, we expect one conversation in the response

    def test_conversation_create(self):
        response = self.client.post(reverse('conversations-list-create'), data={'title': 'New Conversation'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 2) # Since we already had one conversation and created a new one, we expect two conversations in total
        self.assertEqual(Conversation.objects.get(id=response.data['id']).title, 'New Conversation')