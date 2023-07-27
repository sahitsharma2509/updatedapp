# authentication/management/commands/update_user_tokens.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from authentication.models import Message

User = get_user_model()

class Command(BaseCommand):
    help = 'Update user tokens from existing messages'

    def handle(self, *args, **options):
        for user in User.objects.all():
            # Calculate the total tokens used by this user
            total_tokens = 0
            for message in Message.objects.filter(conversation__user=user):
                total_tokens += message.token_length

            # Assign the calculated total tokens to the user's profile
            user.profile.tokens_used = total_tokens
            user.profile.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated user tokens'))
