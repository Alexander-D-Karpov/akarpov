# Generated by Django 4.2 on 2023-04-07 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0010_fileintrash"),
    ]

    operations = [
        migrations.AddField(
            model_name="file",
            name="file_type",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="file",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="file",
            name="name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
