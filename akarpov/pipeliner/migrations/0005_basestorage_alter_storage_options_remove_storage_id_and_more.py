# Generated by Django 4.1.4 on 2023-01-01 21:26

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("pipeliner", "0004_multiplicationblock_storage_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseStorage",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "polymorphic_ctype",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="polymorphic_%(app_label)s.%(class)s_set+",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
        ),
        migrations.AlterModelOptions(
            name="storage",
            options={"base_manager_name": "objects"},
        ),
        migrations.RemoveField(
            model_name="storage",
            name="id",
        ),
        migrations.CreateModel(
            name="RunnerStorage",
            fields=[
                (
                    "basestorage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="pipeliner.basestorage",
                    ),
                ),
                ("data", models.JSONField(default=dict)),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("pipeliner.basestorage",),
        ),
        migrations.AddField(
            model_name="storage",
            name="basestorage_ptr",
            field=models.OneToOneField(
                auto_created=True,
                default=123,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                serialize=False,
                to="pipeliner.basestorage",
            ),
            preserve_default=False,
        ),
    ]