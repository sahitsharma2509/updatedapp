# Generated by Django 4.2 on 2023-07-26 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0032_auto_20230725_1651"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="tokens_remaining",
            field=models.IntegerField(default=0),
        ),
    ]