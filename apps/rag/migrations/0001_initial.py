import pgvector.django
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # CREATE EXTENSION IF NOT EXISTS vector;  (no manual psql step needed)
        pgvector.django.VectorExtension(),
        migrations.CreateModel(
            name='Segment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('segment_id', models.CharField(max_length=100, unique=True)),
                ('video_id', models.CharField(blank=True, max_length=100)),
                ('time_range', models.CharField(blank=True, max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('summary', models.TextField(blank=True)),
                ('keywords', models.JSONField(blank=True, default=list)),
                ('possible_questions', models.JSONField(blank=True, default=list)),
                ('embedding', pgvector.django.VectorField(dimensions=384)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'rag_segments',
            },
        ),
    ]
