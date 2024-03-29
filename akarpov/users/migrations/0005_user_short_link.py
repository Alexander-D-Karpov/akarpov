# Generated by Django 4.1.7 on 2023-03-16 11:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("shortener", "0001_initial"),
        ("users", "0004_remove_user_short_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="short_link",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="shortener.link",
            ),
        ),
    ]
