# Generated by Django 4.2 on 2023-04-22 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0019_alter_basefileitem_options_alter_file_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="folder",
            name="size",
            field=models.IntegerField(default=0),
        ),
    ]
