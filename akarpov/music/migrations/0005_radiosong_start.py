# Generated by Django 4.2.3 on 2023-07-09 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("music", "0004_radiosong"),
    ]

    operations = [
        migrations.AddField(
            model_name="radiosong",
            name="start",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
