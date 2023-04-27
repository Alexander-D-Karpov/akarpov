# Generated by Django 4.2 on 2023-04-22 09:07

import akarpov.files.services.files
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    replaces = [
        ("files", "0001_initial"),
        ("files", "0002_alter_basefile_options_alter_folder_options_and_more"),
        ("files", "0003_basefile_short_link_folder_short_link"),
        ("files", "0004_alter_basefile_short_link_alter_folder_short_link"),
        ("files", "0005_alter_basefile_description_alter_basefile_folder_and_more"),
        ("files", "0006_alter_basefile_slug"),
        ("files", "0007_file_alter_folder_parent_delete_basefile_file_folder_and_more"),
        ("files", "0008_file_completed_on_file_created_on_file_filename_and_more"),
        ("files", "0009_remove_file_completed_on_remove_file_created_on_and_more"),
        ("files", "0010_fileintrash"),
        ("files", "0011_file_file_type_alter_file_description_and_more"),
        ("files", "0012_alter_file_options_alter_file_file"),
        ("files", "0013_alter_file_options"),
        ("files", "0014_alter_fileintrash_file"),
        ("files", "0015_fileintrash_name"),
        ("files", "0016_alter_file_file_type_alter_file_name"),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("shortener", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Folder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(blank=True, max_length=20)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="files.folder",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files_folders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "short_link",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shortener.link",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="FileInTrash",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=akarpov.files.services.files.trash_file_upload
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trash_files",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=200)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="File",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(blank=True, max_length=20, unique=True)),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("private", models.BooleanField(default=True)),
                ("preview", models.FileField(blank=True, upload_to="file/previews/")),
                (
                    "file",
                    models.FileField(
                        upload_to=akarpov.files.services.files.user_unique_file_upload
                    ),
                ),
                (
                    "folder",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="files.folder",
                    ),
                ),
                (
                    "short_link",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shortener.link",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("file_type", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "abstract": False,
                "ordering": ["-modified"],
            },
        ),
    ]