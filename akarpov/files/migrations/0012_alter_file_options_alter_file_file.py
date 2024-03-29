# Generated by Django 4.2 on 2023-04-08 08:12

import akarpov.files.services.files
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0011_file_file_type_alter_file_description_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="file",
            options={"ordering": ["modified"]},
        ),
        migrations.AlterField(
            model_name="file",
            name="file",
            field=models.FileField(
                upload_to=akarpov.files.services.files.user_unique_file_upload
            ),
        ),
    ]
