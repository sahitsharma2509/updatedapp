from django.shortcuts import render, redirect , get_object_or_404
from django.http import HttpResponse,HttpResponseBadRequest
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from up_dated import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from . tokens import generate_token
from .search import qsearch
from .loaders import readFile,get_response
from .baby_agent import get_baby_agi_response
from authentication.models import Conversation ,PdfDocument , Message , Vectorstore , YouTubeLink , KnowledgeDocument , Knowledgebase
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
from .serializers import MessageSerializer,ConversationSerializer,UserSerializer,PdfDocumentSerializer,KnowledgebaseSerializer
from .utils import getMessage
from .youtube import readYoutube
from django.http import JsonResponse
from rest_framework.parsers import JSONParser

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


# Create your views here.
def home(request):
    return render(request, "authentication/index.html")

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
def upload_single_pdf(request):
    if request.method == 'POST':
        try:
            pdf_file = request.FILES['file']
        except MultiValueDictKeyError:
            return JsonResponse({'upload_failed': 'Please upload a PDF file.'}, status=400)

        try:
            validate_pdf_file(pdf_file)
        except ValidationError as e:
            return JsonResponse({'upload_failed': str(e)}, status=400)

        pdf_path = default_storage.save('pdf_documents/' + pdf_file.name, pdf_file)
        user = request.user
        user_id = user.id

        user = User.objects.filter(id=user_id).first()
        # Truncate file name if it's longer than 50 characters
        file_name = pdf_file.name[:50]


        pdf_doc = PdfDocument.objects.create(user=user, document=pdf_path, name=file_name)

        request.session['pdf_document_id'] = pdf_doc.id
        index_name = "test"

        # Process and embed the PDF file
        pinecone_index = readFile(user, pdf_doc)


       

        # Store Pinecone index in cache
        cache_key = f'pinecone_index:{user.id}:{pdf_doc.id}'
        cache.set(cache_key, pinecone_index)

        return JsonResponse({'upload_success': 'Upload Successful','pdf_document_id': pdf_doc.id})

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def store_youtube_url(request):
    if request.method == 'POST':
        try:
            url = request.data.get('url')
        except KeyError:
            return JsonResponse({'error': 'No URL provided.'}, status=400)

        # Validate URL
        validate = URLValidator()
        try:
            validate(url)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)

        # Check if it's a YouTube URL
        youtube_pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
        if not re.match(youtube_pattern, url):
            return JsonResponse({'error': 'Invalid YouTube URL.'}, status=400)

        user = request.user
        yt_link = YouTubeLink.objects.create(user=user, url=url)

        # Update Pinecone index here based on the YouTube URL
        # You will have to define this function
        pinecone_index = readYoutube(user, yt_link)

        # Store Pinecone index in cache
        cache_key = f'pinecone_index:{user.id}:{yt_link.id}'
        cache.set(cache_key, pinecone_index)

        return JsonResponse({'success': 'YouTube URL stored successfully', 'yt_link_id': yt_link.id})

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def index_document(user,document):
    # Determine the type of the document
    if document.data['url'].startswith('http'):
        # This is a URL, so we'll assume it's a YouTube link
        # You might want to add more robust checking here
        pinecone_index = readYoutube(user, document)
        pass
    elif document.data['url'].endswith('.pdf'):
        # This is not a URL, so we'll assume it's a file
        # You might want to add more robust checking here
        pinecone_index = readFile(user, document)
        pass
    
    # Store Pinecone index in cache
    cache_key = f'pinecone_index:{user.id}:{document.id}'
    cache.set(cache_key, pinecone_index)




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
        knowledge_base = Knowledgebase.objects.create(name=name, user=user)

        # Process the inputs
        i = 0
        while True:
            type = request.POST.get(f'inputs[{i}][type]')
            if type is None:
                break

            file = request.FILES.get(f'inputs[{i}][data][file]')
            url = request.POST.get(f'inputs[{i}][data][url]')
            
            # Handle the input based on its type
            if type == 'YouTube':
                document_data = {'name': url, 'url': url}
                document = KnowledgeDocument.objects.create(document_type=type, data=document_data)
                knowledge_base.documents.add(document)
                print("Document", document)
                index_document(user, document)
            elif type == 'PDF':
                # The content in this case should be a file
                if not file:
                    return Response({'detail': 'PDF file is required.'}, status=status.HTTP_400_BAD_REQUEST)

                # Check if file is a valid PDF file here (not included in this code)

                # Save the file and create a Document for it
                filename = default_storage.save(file.name, file)
                document_data = {'name': filename, 'url': filename}
                document = KnowledgeDocument.objects.create(document_type=type, data=document_data)
                knowledge_base.documents.add(document)
                print("Document", document)
                index_document(user, document)

            else:
                return Response({'detail': 'Invalid input type.'}, status=status.HTTP_400_BAD_REQUEST)

            i += 1

    return Response({'detail': 'Knowledge base created.'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_knowledgebases(request):
    knowledgebases = Knowledgebase.objects.filter(user=request.user).order_by('-timestamp')
    serializer = KnowledgebaseSerializer(knowledgebases, many=True)
    return Response(serializer.data)




@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_knowledgebase(request, knowledgebase_id):
    try:
        knowledge_base = Knowledgebase.objects.get(id=knowledgebase_id, user=request.user)
    except Knowledgebase.DoesNotExist:
        return Response({'detail': 'Knowledge base not found.'}, status=status.HTTP_404_NOT_FOUND)

    knowledge_base.delete()
    return Response({'detail': 'Knowledge base deleted.'}, status=status.HTTP_204_NO_CONTENT)




def validate_pdf_file(file):
    if not file.name.endswith('.pdf'):
        raise ValidationError('Please upload a PDF file.')
    if file.size >settings.MAX_PDF_SIZE:
        raise ValidationError(f"File size must be less than {settings.MAX_PDF_SIZE/1000} KB.")
    

@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def answer(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(f"Received data: {data}") 
        conversation_id = data.get('conversation')
        is_user = data.get('is_user')
        text = data.get('text')
        user_id = request.user
        conversation = Conversation.objects.get(pk=conversation_id)
        pdf_id = conversation.pdf_document
        print("PDF_id",pdf_id)
        # Check if Pinecone index object is already in cache
        cache_key = f'pinecone_index_v2:{user_id}:{pdf_id}'
        cache_value = cache.get(cache_key)
        pinecone_index = cache_value.get('index', None) if cache_value else None
        namespace = cache_value.get('namespace', None) if cache_value else None
        if pinecone_index is None:
            try:
                vectorstore = Vectorstore.objects.get(user=user_id, document_id=pdf_id)
                pinecone_index = vectorstore.index
                namespace = vectorstore.namespace
                cache.set(cache_key, {'index': pinecone_index, 'namespace': namespace})


            except Vectorstore.DoesNotExist:
                # Handle the case where the Vectorstore does not exist
                pass
        print(text)
        print(str(pinecone_index))
        print(namespace)
        response = get_response(text, str(pinecone_index),namespace)  #LAST STEP
        message_user = Message.objects.create(conversation=conversation, is_user=True, text=text)
        message_bot = Message.objects.create(conversation=conversation, is_user=False, text=response) 
        response_data = {'output': response}
        print(response)
        return JsonResponse(response_data, status=200)

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





class PdfDocumentListCreateView(generics.ListCreateAPIView):
    queryset = PdfDocument.objects.all()
    serializer_class = PdfDocumentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Message.objects.filter(conversation=conversation_id).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        conversation_id = self.kwargs['conversation_id']
        return getMessage(request, conversation_id)



class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        conversation = Conversation.objects.filter(user=user).order_by('-created_at')
        return conversation

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)





@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def create_conversation(request):
    try:
        user = request.user

        knowledgebase_id = request.data.get('knowledge_base_id', None)

        if knowledgebase_id is not None:
            knowledgebase = get_object_or_404(Knowledgebase, id=knowledgebase_id)
            conversation = Conversation.objects.create(user=user, knowledge_base=knowledgebase)
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




        

class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        print("CurrentUserView.get_object called")
        print(f"User: {self.request.user}")
        return self.request.user
    
class CustomTokenObtainPairView(TokenObtainPairView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
       
        data = json.loads(request.body)
        print(data)
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

        # If the user is authenticated, log them in and return a token pair
        if user is not None:
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
