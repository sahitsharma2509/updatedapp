# Generated by Django 4.2 on 2023-06-26 13:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0025_rename_text_chunk_content_chunk_metadata"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="youtubelink",
            name="user",
        ),
        migrations.DeleteModel(
            name="PdfDocument",
        ),
        migrations.DeleteModel(
            name="YouTubeLink",
        ),
    ]