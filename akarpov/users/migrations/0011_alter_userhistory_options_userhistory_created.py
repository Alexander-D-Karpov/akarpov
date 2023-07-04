# Generated by Django 4.2.2 on 2023-07-04 09:55

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_userhistory_description_alter_userhistory_name"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="userhistory",
            options={"ordering": ["-created"]},
        ),
        migrations.AddField(
            model_name="userhistory",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
