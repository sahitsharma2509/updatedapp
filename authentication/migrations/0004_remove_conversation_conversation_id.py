# Generated by Django 4.2 on 2023-04-14 19:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0003_alter_message_conversation"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="conversation",
            name="conversation_id",
        ),
    ]
