# Generated by Django 4.1.7 on 2023-03-15 12:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("shortener", "0001_initial"),
        ("blog", "0002_alter_comment_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="short_link",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="shortener.link",
            ),
        ),
    ]