# Generated by Django 4.1.7 on 2023-02-26 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_platform", "0003_alter_numberrangequestion_number_range_max_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="numberquestion",
            name="correct_answer",
            field=models.IntegerField(blank=True),
        ),
    ]
