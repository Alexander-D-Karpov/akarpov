# Generated by Django 4.2.4 on 2023-08-06 06:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("shortener", "0004_alter_linkviewmeta_options"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="link",
            table="short_link",
        ),
    ]