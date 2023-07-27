from django.db import migrations

def calculate_tokens_remaining(apps, schema_editor):
    UserProfile = apps.get_model('authentication', 'UserProfile')
    for profile in UserProfile.objects.all():
        profile.tokens_remaining = profile.plan.token_limit - profile.tokens_used
        profile.save()

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0033_userprofile_tokens_remaining'),  # This will be different in your file
    ]

    operations = [
        migrations.RunPython(calculate_tokens_remaining),
    ]
