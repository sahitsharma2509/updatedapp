from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
import debug_toolbar
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('signup', views.signup, name='signup'),
    path('check_user_exists', views.check_user_exists, name='check_user_exists'),
    path('signout', views.signout, name='signout'),
    path('api/upload/single', views.upload_single_pdf, name='upload_single_pdf'),
    path('api/yt', views.store_youtube_url, name='store_youtube_url'),
    path('answer',views.answer, name='answer'),
    path('chat/with-list/<int:conversation_id>/', views.MessageListView.as_view(), name='message-list'),
    path('chat/', views.ConversationListCreateView.as_view(), name='conversations-list-create'),
    path('chat/message/',views.create_message, name='create_message'),
    path('chat/baby_agi/',views.baby_agi_message, name='baby_agi_message'),
    path('chat/knowledge/',views.chat_knowledge, name='chat_knowledge'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
    path('chat/conversations/',views.create_conversation, name='create_conversation'),
    path('pdf/', views.PdfDocumentListCreateView.as_view(), name='pdf-list-create'),
    path('create_knowledgebase/', views.create_knowledgebase, name='create_knowledgebase'),
    path('get_knowledgebases/', views.get_knowledgebases, name='get_knowledgebases'),
    path('delete_knowledgebase/<int:knowledgebase_id>/', views.delete_knowledgebase, name='delete_knowledgebase'),
     path('knowledgebases/', views.get_knowledgebases, name='get_knowledgebases'),
    

   

    #path('stream_response/', views.stream_response, name='stream_response'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
