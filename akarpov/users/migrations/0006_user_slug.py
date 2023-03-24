# Generated by Django 4.1.7 on 2023-03-24 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_user_short_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="slug",
            field=models.SlugField(blank=True, max_length=20, unique=True),
        ),
    ]
