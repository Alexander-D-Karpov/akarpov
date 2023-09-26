from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    dependencies = [
        ("files", "0024_alter_file_options_alter_filereport_options_and_more"),
    ]

    operations = [VectorExtension()]
