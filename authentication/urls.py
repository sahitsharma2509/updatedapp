from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
import debug_toolbar
from django.conf.urls.static import static
from .views import UserProfileView,UpdateProfileView,FileUploadView


urlpatterns = [
    path('', views.home, name='home'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('signup', views.signup, name='signup'),
    path('check_user_exists', views.check_user_exists, name='check_user_exists'),
    path('signout', views.signout, name='signout'),
    path('chat/with-list/<int:conversation_id>/', views.MessageListView.as_view(), name='message-list'),
    path('chat/', views.ConversationListView.as_view(), name='conversations-list'),
    path('chat/message/',views.create_message, name='create_message'),
    path('chat/baby_agi/',views.baby_agi_message, name='baby_agi_message'),
    path('chat/knowledge/',views.chat_knowledge, name='chat_knowledge'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
    path('chat/conversations/',views.create_conversation, name='create_conversation'),
    path('create_knowledgebase/', views.create_knowledgebase, name='create_knowledgebase'),
    path('get_knowledgebases/', views.get_knowledgebases, name='get_knowledgebases'),
    path('delete_knowledgebase/<int:knowledgebase_id>/', views.delete_knowledgebase, name='delete_knowledgebase'),
     path('knowledgebases/', views.get_knowledgebases, name='get_knowledgebases'),
     path('api/conversations/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
     path('user/profile/', UserProfileView.as_view(), name='user-profile'),
     path('updateProfile/<int:pk>/', UpdateProfileView.as_view(), name='update-profile'),
     path('api/upload/', FileUploadView.as_view()),



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
