# Generated by Django 4.2 on 2023-04-11 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0014_alter_fileintrash_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="fileintrash",
            name="name",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
