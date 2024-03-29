# Generated by Django 4.2.3 on 2023-08-05 08:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("shortener", "0002_alter_link_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="linkviewmeta",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="link_views",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
