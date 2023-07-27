from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from django.apps import apps
from .helpers import get_knowledge_summary
from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned
from django_redis import get_redis_connection
from .models import UserProfile, Message, Plan
from django.contrib.auth.models import User


@receiver(post_save, sender=apps.get_model('authentication', 'Knowledgebase'))
def create_knowledge_summary(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: handle_summary_creation(sender, instance, created, **kwargs))

def handle_summary_creation(sender, instance, created, **kwargs):
    # The original code for handling summary creation goes here.
    # For example:
    KnowledgeBaseSummary = apps.get_model('authentication', 'KnowledgeBaseSummary')
    if created:  
        try:
            summary_instance = KnowledgeBaseSummary.objects.get(knowledgebase=instance)
            summary = summary_instance.summary
        except KnowledgeBaseSummary.DoesNotExist:
            try:
                summary = get_knowledge_summary(instance)
            except Exception as ex:
                print(f"An error occurred during summary generation: {ex}")
                return
                
            try:
                KnowledgeBaseSummary.objects.create(knowledgebase=instance, summary=summary)
            except Exception as ex:
                print(f"An error occurred during KnowledgeBaseSummary object creation: {ex}")
                return
                
        except MultipleObjectsReturned:
            print("There are multiple KnowledgeBaseSummary objects for this Knowledgebase instance.")
            
        except Exception as ex:
            print(f"An unexpected error occurred: {ex}")

    KnowledgeBaseSummary = apps.get_model('authentication', 'KnowledgeBaseSummary')
    
    if created:  
        try:
            summary_instance = KnowledgeBaseSummary.objects.get(knowledgebase=instance)
            # If summary exists, just retrieve it
            summary = summary_instance.summary
            
        except KnowledgeBaseSummary.DoesNotExist:
            # If summary does not exist, generate and store it
            try:
                summary = get_knowledge_summary(instance)
            except Exception as ex:
                print(f"An error occurred during summary generation: {ex}")
                return
                
            try:
                KnowledgeBaseSummary.objects.create(knowledgebase=instance, summary=summary)
            except Exception as ex:
                print(f"An error occurred during KnowledgeBaseSummary object creation: {ex}")
                return
                
        except MultipleObjectsReturned:
            print("There are multiple KnowledgeBaseSummary objects for this Knowledgebase instance.")
            
        except Exception as ex:
            print(f"An unexpected error occurred: {ex}")





@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if kwargs.get('created', False):  # User has just been created
        free_plan = Plan.objects.get(name='free')
        UserProfile.objects.create(user=instance, avatar='avatar/default.png', plan=free_plan)
    else:  
        try:
            instance.profile.save()
        except UserProfile.DoesNotExist:
            free_plan = Plan.objects.get(name='free')
            UserProfile.objects.create(user=instance, avatar='avatar/default.png', plan=free_plan)


"""
@receiver(post_save, sender=Message)
def update_user_tokens(sender, instance, created, **kwargs):
    if created and not instance.is_user:  # New message created and sender is not user (i.e., sender is AI)
        user = instance.conversation.user
        # Get the sum of all message tokens in the conversation
        total_tokens = instance.conversation.total_token_length
        user.profile.use_tokens(total_tokens)
"""