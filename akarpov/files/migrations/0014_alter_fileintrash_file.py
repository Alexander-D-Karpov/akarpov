# Generated by Django 4.2 on 2023-04-11 10:55

import akarpov.files.services.files
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0013_alter_file_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fileintrash",
            name="file",
            field=models.FileField(
                upload_to=akarpov.files.services.files.trash_file_upload
            ),
        ),
    ]
