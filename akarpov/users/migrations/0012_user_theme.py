# Generated by Django 4.2.6 on 2023-10-25 06:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("themes", "0001_initial"),
        ("users", "0011_alter_userhistory_options_userhistory_created"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="theme",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="themes.theme",
            ),
        ),
    ]
