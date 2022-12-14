# Generated by Django 4.1.5 on 2023-01-11 10:30

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("pipeliner", "0001_initial"),
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
        migrations.CreateModel(
            name="ConstantNumberBlock",
            fields=[
                (
                    "baseblock_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="pipeliner.baseblock",
                    ),
                ),
                ("number", models.DecimalField(decimal_places=2, max_digits=5)),
            ],
            options={
                "abstract": False,
            },
            bases=("pipeliner.baseblock",),
        ),
        migrations.CreateModel(
            name="ConstantStringBlock",
            fields=[
                (
                    "baseblock_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="pipeliner.baseblock",
                    ),
                ),
                ("string", models.TextField()),
            ],
            options={
                "abstract": False,
            },
            bases=("pipeliner.baseblock",),
        ),
        migrations.CreateModel(
            name="MultiplicationBlock",
            fields=[
                (
                    "baseblock_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="pipeliner.baseblock",
                    ),
                ),
                ("by", models.DecimalField(decimal_places=2, max_digits=5)),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("pipeliner.baseblock",),
        ),
        migrations.AddField(
            model_name="baseblock",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="baseblock",
            name="name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="baseblock",
            name="parent",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="pipeliner.baseblock",
            ),
        ),
        migrations.AddField(
            model_name="baseblock",
            name="updated",
            field=models.DateTimeField(auto_now=True),
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
        migrations.CreateModel(
            name="Storage",
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
        migrations.CreateModel(
            name="TrashBlock",
            fields=[
                (
                    "baseblock_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="pipeliner.baseblock",
                    ),
                ),
                (
                    "storage",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="pipeliner.storage",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("pipeliner.baseblock",),
        ),
    ]
