# Generated by Django 4.2.3 on 2023-08-04 13:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("shortener", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="link",
            options={"ordering": ["-modified"]},
        ),
    ]