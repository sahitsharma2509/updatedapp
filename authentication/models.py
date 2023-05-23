from django.db import models
import uuid
from django.contrib.auth.models import User

class PdfDocument(models.Model):
    document = models.FileField(upload_to='pdf_documents/')
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.document.name
    
class YouTubeLink(models.Model):
    url = models.URLField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.name or self.url

    
class Conversation(models.Model):
    CHAT = 'chat'
    PDF = 'pdf'
    YT  = 'yt-chat'
    CONVERSATION_TYPES = [
        (CHAT, 'Chat'),
        (PDF, 'PDF'),
        (YT, 'YT-chat')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    conversation_type = models.CharField(choices=CONVERSATION_TYPES, max_length=50, default=CHAT)
    pdf_document = models.ForeignKey(PdfDocument, null=True, blank=True, on_delete=models.SET_NULL)
    yt_link = models.ForeignKey(YouTubeLink, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=50, null=True, default=None)


    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    is_user = models.BooleanField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)




class Vectorstore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    document = models.ForeignKey(PdfDocument, null=True, on_delete=models.SET_NULL)
    youtube_link = models.ForeignKey(YouTubeLink, null=True, on_delete=models.SET_NULL)
    index = models.CharField(default="test", editable=False)
    namespace = models.CharField(max_length=255, default='')
    
    @property
    def file_path(self):
        if self.document:
            return self.document.document.path
        return ''


