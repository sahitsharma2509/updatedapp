import django
django.setup()

from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db.models import JSONField


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

    
    



class KnowledgeDocument(models.Model):
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('youtube_url', 'YouTube URL'),
        ('csv', 'CSV'),
        ('text', 'Text'),
        ('other', 'Other'),
    ]

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='other',
    )
    data = JSONField()




class Knowledgebase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='')
    documents = models.ManyToManyField(KnowledgeDocument)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class Vectorstore(models.Model):
    knowledgebase = models.ForeignKey(Knowledgebase, on_delete=models.CASCADE)
    document = models.OneToOneField(KnowledgeDocument, on_delete=models.CASCADE)  # Add this line
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    index = models.CharField(default="test", editable=False)
    namespace = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.namespace

    
class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    knowledge_base = models.ForeignKey(Knowledgebase, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=50, null=True, default=None)

    @property
    def document_types(self):
        return ', '.join(self.knowledge_base.documents.values_list('document_type', flat=True))
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    is_user = models.BooleanField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)