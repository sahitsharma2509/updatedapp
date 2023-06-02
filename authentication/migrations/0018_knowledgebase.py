# Generated by Django 4.2 on 2023-05-23 10:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("authentication", "0017_vectorstore_youtube_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="Knowledgebase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(default="", max_length=255)),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("pdf", "PDF"),
                            ("youtube_url", "YouTube URL"),
                            ("csv", "CSV"),
                            ("text", "Text"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=20,
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("document_data", models.JSONField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vectorstore",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="authentication.vectorstore",
                    ),
                ),
            ],
        ),
    ]
