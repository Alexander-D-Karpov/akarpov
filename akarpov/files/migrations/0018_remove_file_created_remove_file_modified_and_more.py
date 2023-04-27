# Generated by Django 4.2 on 2023-04-22 09:21

from django.db import migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0017_alter_folder_options_rename_file_file_file_obj_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="file",
            name="created",
        ),
        migrations.RemoveField(
            model_name="file",
            name="modified",
        ),
        migrations.RemoveField(
            model_name="folder",
            name="created",
        ),
        migrations.RemoveField(
            model_name="folder",
            name="modified",
        ),
        migrations.AddField(
            model_name="basefileitem",
            name="created",
            field=model_utils.fields.AutoCreatedField(
                default=django.utils.timezone.now,
                editable=False,
                verbose_name="created",
            ),
        ),
        migrations.AddField(
            model_name="basefileitem",
            name="modified",
            field=model_utils.fields.AutoLastModifiedField(
                default=django.utils.timezone.now,
                editable=False,
                verbose_name="updated",
            ),
        ),
    ]