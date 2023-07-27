from django.db import migrations

def assign_free_plan_to_existing_profiles(apps, schema_editor):
    UserProfile = apps.get_model('authentication', 'UserProfile')
    Plan = apps.get_model('authentication', 'Plan')
    free_plan = Plan.objects.get(name='free')
    UserProfile.objects.filter(plan__isnull=True).update(plan=free_plan)

class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0031_plan_userprofile_last_reset_userprofile_tokens_used_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(assign_free_plan_to_existing_profiles),
    ]
