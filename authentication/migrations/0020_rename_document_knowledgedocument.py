# Generated by Django 4.2 on 2023-05-28 21:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentication",
            "0019_document_remove_conversation_conversation_type_and_more",
        ),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Document",
            new_name="KnowledgeDocument",
        ),
    ]