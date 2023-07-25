from django.shortcuts import render, redirect , get_object_or_404
from django.http import HttpResponse,HttpResponseBadRequest
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from up_dated import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate, login, logout
from .search import qsearch
from .loaders import index_document,get_loader,load_and_split_documents,run_summary_chain,IndexingContext
from .response import get_response
from .baby_agent import get_baby_agi_response
from authentication.models import Conversation  , Message , Vectorstore  , KnowledgeDocument , Knowledgebase, KnowledgeBaseSummary, UserProfile
from django.http import HttpResponseServerError,StreamingHttpResponse
import datetime
from django.core.files.storage import default_storage
import pickle
from django.urls import reverse
import base64,time 
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.datastructures import MultiValueDictKeyError
from django.conf import settings
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics
from rest_framework.response import Response
from .serializers import MessageSerializer,ConversationSerializer,UserSerializer,KnowledgebaseSerializer, UserProfileSerializer,KnowledgeDocumentSerializer
from .utils import getMessage
from .youtube import readYoutube
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from cacheops import cached_as,invalidate_model
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import re
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes, authentication_classes,api_view
from django.views.decorators.http import require_http_methods
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from rest_framework.decorators import parser_classes
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.pagination import PageNumberPagination
from django_redis import get_redis_connection
from uuid import uuid4
from django.http import FileResponse
import requests
import os
from django.core.files import File


# Create your views here.
def home(request):
    return render(request, "authentication/index.html")


def text_to_speech(request):
    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream"

    headers = {
      "Accept": "audio/mpeg",
      "Content-Type": "application/json",
      "xi-api-key": "655568d6c24d8fb6e9d3834712a0504c"
    }

    # Assume 'text' is passed as a GET parameter
    text = request.GET.get('text', 'Hello world')
    data = {
      "text": text,
      "model_id": "eleven_monolingual_v1",
      "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
      }
    }

    response = requests.post(url, json=data, headers=headers, stream=True)

    filename = 'output.mp3'
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
    
    # Assuming files are in a directory named 'media' in your project
    file_path = os.path.join('media', filename)

    # Serve file as attachment so it can be downloaded
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    return response

@csrf_exempt
def signup(request):
    if request.method == "POST":
        # Load JSON data from the request body
        data = json.loads(request.body)
        
        username = data['username']
        fname = data['name']
        lname = data['surname']
        email = data['email']
        pass1 = data['password']
        
        if User.objects.filter(username=username):
            response = {'success': False, 'message': 'Username already exists. Please try a different username.'}
            return JsonResponse(response)
        
        if User.objects.filter(email=email).exists():
            response = {'success': False, 'message': 'Email already registered.'}
            return JsonResponse(response)
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = True
        myuser.save()
        response = {'success': True, 'message': 'Your account has been created successfully. Please check your email to confirm your email address in order to activate your account.'}
        return JsonResponse(response)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@csrf_exempt
def check_user_exists(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['username']
        
        user_exists = User.objects.filter(username=username).exists()
        
        return JsonResponse({'exists': user_exists})





def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')




@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def create_knowledgebase(request):
    user = request.user
    # Ensure the name is provided
    name = request.POST.get('name')
    if not name:
        return Response({'detail': 'Knowledge base name is required.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # Create the knowledge base
        namespace = str(uuid4())
        knowledge_base = Knowledgebase.objects.create(name=name, user=user, namespace=namespace)

        # Process the inputs
        i = 0
        while True:
            type = request.POST.get(f'inputs[{i}][type]')
            if type is None:
                break

            file = request.FILES.get(f'inputs[{i}][data][file]')
            url = request.POST.get(f'inputs[{i}][data][url]')
            
            # Get the loader based on the document type
            loader = get_loader(document_type=type, url=url, file=file)
            documents, texts = load_and_split_documents(loader)
            
            # Create a KnowledgeDocument and add it to the knowledge base
            document_data = {'name': url or file.name, 'url': url or file.name}
            document = KnowledgeDocument.objects.create(document_type=type, data=document_data)
            knowledge_base.documents.add(document)
            
            # Index the document
           
            context = IndexingContext(user, namespace, knowledge_base, document, texts)
            index_document(context)

            summary = run_summary_chain(documents)
            KnowledgeBaseSummary.objects.create(knowledgebase=knowledge_base, summary=summary)

            i += 1

    invalidate_model(knowledge_base)
    return Response({'detail': 'Knowledge base created.'}, status=status.HTTP_201_CREATED)


@cached_as(Knowledgebase, timeout=60*15)
def get_knowledgebases_data(user):
    knowledgebases = Knowledgebase.objects.filter(user=user).order_by('-timestamp')
    serializer = KnowledgebaseSerializer(knowledgebases, many=True)
    return serializer.data


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_knowledgebases(request):
    # We fetch the data (this step is cached)
    data = get_knowledgebases_data(request.user)
    # Then we wrap it in a Response object and return it
    return Response(data)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_knowledgebase(request, knowledgebase_id):
    try:
        knowledge_base = Knowledgebase.objects.get(id=knowledgebase_id, user=request.user)
    except Knowledgebase.DoesNotExist:
        return Response({'detail': 'Knowledge base not found.'}, status=status.HTTP_404_NOT_FOUND)

    knowledge_base.delete()
    return Response({'detail': 'Knowledge base deleted.'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({'detail': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)

    conversation.delete()
    return Response({'detail': 'Conversation deleted.'}, status=status.HTTP_204_NO_CONTENT)



def validate_pdf_file(file):
    if not file.name.endswith('.pdf'):
        raise ValidationError('Please upload a PDF file.')
    if file.size >settings.MAX_PDF_SIZE:
        raise ValidationError(f"File size must be less than {settings.MAX_PDF_SIZE/1000} KB.")
    


def stream_response_generator(response):
    for data in response:
        yield data




@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def chat_knowledge(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(f"Received data: {data}") 

        conversation_id = data.get('conversation')
        is_user = data.get('is_user')
        text = data.get('text')
        user_id = request.user
        conversation = Conversation.objects.get(pk=conversation_id)

        knowledgebase  = conversation.knowledge_base

        if knowledgebase is not None:
            print(f"Working with Knowledgebase link: {knowledgebase.name}")

        cache_key = f'pinecone_index_v2:{user_id}:{knowledgebase.id}'
        cache_value = cache.get(cache_key)
        pinecone_index = cache_value.get('index', None) if cache_value else None
        namespace = cache_value.get('namespace', None) if cache_value else None

        if pinecone_index is None:
            try:
                vectorstore = Vectorstore.objects.filter(user=user_id, knowledgebase_id=knowledgebase.id).first()
                pinecone_index = vectorstore.index
                namespace = vectorstore.namespace
                cache.set(cache_key, {'index': pinecone_index, 'namespace': namespace})
            except Vectorstore.DoesNotExist:
                # Handle the case where the Vectorstore does not exist
                pass
        print(text)
        print(str(pinecone_index))
        print(namespace)
        response = get_response(text, str(pinecone_index), namespace)  #LAST STEP
        message_user = Message.objects.create(conversation=conversation, is_user=True, text=text)
        message_bot = Message.objects.create(conversation=conversation, is_user=False, text=response) 
        print(type(response))
        print(response)

        # Send a message to the group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation_id}",  # The group name
            {
                "type": "chat.message",  # The method name in your consumer
                "message": response,
                "username": request.user.username,
            },
        )

        return StreamingHttpResponse(stream_response_generator(response),content_type="text/plain", status=200)


    
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Message.objects.filter(conversation=conversation_id).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        conversation_id = self.kwargs['conversation_id']
        return getMessage(request, conversation_id)


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(user=user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        page_number = request.query_params.get('page') or '1'
        cache_key = f'conversations:{request.user.id}:page:{page_number}'
        print(f"Looking up key: {cache_key}")  # Add this line
        data = cache.get(cache_key)

        
        if not data:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = self.get_paginated_response(serializer.data).data
            else:
                serializer = self.get_serializer(queryset, many=True)
                data = serializer.data


        return Response(data)

    


@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def create_conversation(request):
    print("create_conversation called")  
    try:
        user = request.user
        knowledgebase_id = request.data.get('knowledge_base_id', None)

        if knowledgebase_id is not None:
            knowledgebase = get_object_or_404(Knowledgebase, id=knowledgebase_id)
            conversation = Conversation.objects.create(user=user, knowledge_base=knowledgebase)

            # After the conversation is created, get the corresponding KnowledgeBaseSummary
            try:
                summary = KnowledgeBaseSummary.objects.get(knowledgebase_id=knowledgebase_id)
                print("Summary",summary)
            except ObjectDoesNotExist:
                # Handle the case when there's no summary for this knowledgebase
                summary = None

            # If there is a summary, create an initial bot message
            if summary:
                initial_message = Message(conversation=conversation, 
                                          text=summary.summary, 
                                          is_user=False)
                initial_message.save()

        else:
            conversation = Conversation.objects.create(user=user)

        return JsonResponse({'conversation_id': conversation.id}, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@api_view(['POST'])
@authentication_classes([JWTAuthentication])
def create_message(request):
    try:
        data = json.loads(request.body)
        print(f"Received data: {data}") 
        conversation_id = data.get('conversation')
        is_user = data.get('is_user')
        text = data.get('text')
        user_id = request.user

        if not (conversation_id and is_user is not None and text and user_id):
            return JsonResponse({"status": "error", "message": "Invalid request data"}, status=400)

        conversation = Conversation.objects.get(pk=conversation_id)  # Get the conversation object
        output = qsearch(text)
        message_user = Message.objects.create(conversation=conversation, is_user=True, text=text)
        message_bot = Message.objects.create(conversation=conversation, is_user=False, text=output['output'])

        response_data = {'output': output}
        return JsonResponse(response_data, status=200)

    except Conversation.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Conversation not found"}, status=404)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
def baby_agi_message(request):
    try:
        data = json.loads(request.body)
        print(f"Received data: {data}") 
        conversation_id = data.get('conversation')
        is_user = data.get('is_user')
        text = data.get('text')
        user_id = request.user

        if not (conversation_id and is_user is not None and text and user_id):
            return JsonResponse({"status": "error", "message": "Invalid request data"}, status=400)

        conversation = Conversation.objects.get(pk=conversation_id)  # Get the conversation object
        output = get_baby_agi_response(text)
        message_user = Message.objects.create(conversation=conversation, is_user=True, text=text)
        message_bot = Message.objects.create(conversation=conversation, is_user=False, text=output['history'])

        response_data = {'output': output}
        print(response_data)
        return JsonResponse(response_data, status=200)

    except Conversation.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Conversation not found"}, status=404)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    


class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        file = request.FILES['file']
        print("Received file: ", file.name)  # Print received file name
        file_name = default_storage.save(file.name, file)
        print("Saved file as: ", file_name)  # Print saved file name

        content_type = file.content_type
        print("File content type: ", content_type)  # Print content type of file
        full_file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        conversation_id = request.POST.get('conversation_id')
        print(conversation_id)
        conversation = Conversation.objects.get(id=conversation_id)
        knowledgebase = conversation.knowledge_base


        if content_type == 'application/pdf':
            document_type = 'PDF'
        elif content_type == 'text/plain':
            document_type = 'text'
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            document_type = 'docx'
        else:
            return Response({"error": "Invalid file type."}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare data for KnowledgeDocument instance
        data = {
            "url": file_name,
            "name": file.name
        }

        # Create KnowledgeDocument instance
        document = KnowledgeDocument.objects.create(
            document_type=document_type,
            data=data,
        )
        print("Created KnowledgeDocument: ", document.id)  # Print ID of created document

        try:
            # Load the document and create embeddings
            print("Loading the document and creating embeddings")
            loader = get_loader(document_type, file=full_file_path)
            documents, texts = load_and_split_documents(loader)
            ctx = IndexingContext(
                user=request.user,
                namespace=knowledgebase.namespace,
                knowledgebase=knowledgebase,
                document=document,
                texts=texts,
            )
            index_document(ctx)
            print("Finished indexing document")
        except Exception as e:
            print("Exception occurred while processing file: ", str(e))  # Print exception details
            return Response({"error": "Error processing file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = KnowledgeDocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)




        

class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile  # assuming a related_name of 'profile' on the UserProfile model

    
class CustomTokenObtainPairView(TokenObtainPairView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        username = data.get('username', '')
        password = data.get('password', '')
        cache_key = f'user:{username}'

        # Check if user object is already in cache
        user = cache.get(cache_key)

        # If the user object is not in the cache, try to authenticate
        if user is None:
            user = authenticate(request, username=username, password=password)

            # If the user is authenticated, store the user object in the cache
            if user is not None:
                cache.set(cache_key, user, timeout=300)

        # If the user is authenticated, create UserProfile if it doesn't exist, log them in and return a token pair
        if user is not None:
            UserProfile.objects.get_or_create(user=user, defaults={
                'avatar': File(open(os.path.join('up_dated', 'media', 'avatar', 'default.png'), 'rb'))
            })
            login(request, user)
            return super().post(request, *args, **kwargs)

        # If the user is not authenticated, return an error response
        else:
            return JsonResponse({'message': 'Bad Credentials!', 'status': 'error'}, status=401)

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            refresh_token_obj = RefreshToken(refresh_token)
            new_access_token = str(refresh_token_obj.access_token)
            new_refresh_token = str(refresh_token_obj)
            return Response({'access': new_access_token, 'refresh': new_refresh_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        

class UpdateProfileView(generics.UpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return UserProfile.objects.get(pk=self.kwargs['pk'])


