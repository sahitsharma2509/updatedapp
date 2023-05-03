# Generated by Django 4.2 on 2023-04-13 20:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_vectorstore_delete_pindex"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="conversation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="authentication.conversation",
            ),
        ),
    ]