# Generated by Django 4.0.8 on 2022-12-07 10:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pipeliner', '0002_baseblock_created_baseblock_name_baseblock_parent_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConstantNumberBlock',
            fields=[
                ('baseblock_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pipeliner.baseblock')),
                ('number', models.DecimalField(decimal_places=2, max_digits=5)),
            ],
            options={
                'abstract': False,
            },
            bases=('pipeliner.baseblock',),
        ),
        migrations.CreateModel(
            name='ConstantStringBlock',
            fields=[
                ('baseblock_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pipeliner.baseblock')),
            ],
            options={
                'abstract': False,
            },
            bases=('pipeliner.baseblock',),
        ),
    ]