# authentication/management/commands/update_plans.py

import json
from django.core.management.base import BaseCommand
from authentication.models import Plan,UserProfile

class Command(BaseCommand):
    help = 'Update plans from config file'

    def handle(self, *args, **options):
        with open('authentication/plans.json', 'r') as f:
            plans = json.load(f)

        for plan_name, token_limit in plans.items():
            plan, created = Plan.objects.get_or_create(
                name=plan_name, 
                defaults={'token_limit': token_limit}
            )

            if not created:
                token_diff = token_limit - plan.token_limit  # calculate the difference between new and old limit
                plan.token_limit = token_limit
                plan.save()

                # Adjust tokens_remaining of all user profiles associated with this plan
                for profile in UserProfile.objects.filter(plan=plan):
                    profile.tokens_remaining = max(profile.tokens_remaining + token_diff, 0)
                    profile.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated plans'))

