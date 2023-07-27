

from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db.models import JSONField
import tiktoken
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.db import transaction


from dateutil.relativedelta import relativedelta
tokenizer = tiktoken.get_encoding('cl100k_base')

# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(text, disallowed_special=())
    return len(tokens)

class Plan(models.Model):
    name = models.CharField(max_length=50)
    token_limit = models.IntegerField()

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    tokens_used = models.IntegerField(default=0)
    tokens_remaining = models.IntegerField(default=0)
    last_reset = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username
    
    def check_and_reset_tokens(self):
        if timezone.now() > self.last_reset + relativedelta(months=1):
            self.tokens_used = 0
            self.tokens_remaining = self.plan.token_limit  # resetting remaining tokens to full limit
            self.last_reset = timezone.now()
            self.save()


    def can_use_tokens(self, tokens_needed):
        self.check_and_reset_tokens()
        return self.tokens_used + tokens_needed <= self.plan.token_limit

    def use_tokens(self, tokens_needed):
        self.check_and_reset_tokens()
        
        if self.can_use_tokens(tokens_needed):
            self.tokens_used += tokens_needed
        else:
            self.tokens_used = self.plan.token_limit

        # Calculate the number of tokens remaining
        self.tokens_remaining = self.plan.token_limit - self.tokens_used

        self.save()
        self.refresh_from_db()

        # Return the number of tokens remaining
        return self.tokens_remaining







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
    content = models.TextField(blank=True, null=True)
    
class Knowledgebase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='')
    namespace = models.CharField(max_length=255)  # Add this line
    documents = models.ManyToManyField(KnowledgeDocument)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name    






class KnowledgeBaseSummary(models.Model):
    knowledgebase = models.ForeignKey(Knowledgebase, on_delete=models.CASCADE)
    summary = models.TextField()

    def __str__(self):
        return self.knowledgebase.namespace  # Access through Knowledgebase

class Vectorstore(models.Model):
    knowledgebase = models.ForeignKey(Knowledgebase, on_delete=models.CASCADE)
    document = models.OneToOneField(KnowledgeDocument, on_delete=models.CASCADE)  # Add this line
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    index = models.CharField(default="test", editable=False)

    def __str__(self):
        return self.knowledgebase.namespace  # Access through Knowledgebase


    
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

    



class Chunk(models.Model):
    vectorstore = models.ForeignKey(Vectorstore, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=36)
    content = models.TextField()
    metadata = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uuid
