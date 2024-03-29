# Generated by Django 4.2 on 2023-04-06 10:37

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_user_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="left_file_upload",
            field=models.IntegerField(
                default=0,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Left file upload(in bites)",
            ),
        ),
    ]
