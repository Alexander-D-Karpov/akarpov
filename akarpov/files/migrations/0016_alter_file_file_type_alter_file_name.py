# Generated by Django 4.2 on 2023-04-14 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0015_fileintrash_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="file_type",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="file",
            name="name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
