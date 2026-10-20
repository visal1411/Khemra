# Generated for revised Knowledge RAG schema with 1536d pgvector
import uuid
import django.db.models.deletion
import pgvector.django.vector
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rag', '0002_segments_split_embeddings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Knowledge',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True, null=True)),
                ('source_type', models.CharField(choices=[('video', 'Video'), ('pdf', 'Pdf'), ('text', 'Text')], max_length=20)),
                ('processing_status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'knowledge',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MetadataType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('weight', models.FloatField(default=1.0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'metadata_types',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='KnowledgeSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('language', models.CharField(max_length=10)),
                ('file_data', models.BinaryField(help_text='the actual file bytes')),
                ('duration_seconds', models.FloatField(blank=True, null=True)),
                ('page_count', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('knowledge', models.ForeignKey(db_column='knowledge_id', on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='rag.knowledge')),
            ],
            options={
                'db_table': 'knowledge_sources',
            },
        ),
        migrations.CreateModel(
            name='KnowledgeSegment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('segment_index', models.IntegerField(default=0, help_text='Order index of segment within knowledge')),
                ('transcript', models.TextField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=500, null=True)),
                ('keywords', models.JSONField(blank=True, default=list, null=True)),
                ('possible_questions', models.JSONField(blank=True, default=list, null=True)),
                ('summary', models.TextField(blank=True, null=True)),
                ('start_time_seconds', models.FloatField(blank=True, null=True)),
                ('end_time_seconds', models.FloatField(blank=True, null=True)),
                ('page_start', models.IntegerField(blank=True, null=True)),
                ('page_end', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('knowledge', models.ForeignKey(db_column='knowledge_id', on_delete=django.db.models.deletion.CASCADE, related_name='segments', to='rag.knowledge')),
            ],
            options={
                'db_table': 'knowledge_segments',
                'ordering': ['knowledge', 'segment_index'],
            },
        ),
        migrations.CreateModel(
            name='KnowledgeEmbedding',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('item_index', models.IntegerField(default=0, help_text='0 for title/summary/content; 0,1,2... for keywords/questions')),
                ('title', models.TextField(blank=True, help_text='filled only when this row embeds the title', null=True)),
                ('summary', models.TextField(blank=True, help_text='filled only when this row embeds the summary', null=True)),
                ('keywords', models.JSONField(blank=True, help_text='[{"text": "HR portal", "vector": [0.027, ...]}]', null=True)),
                ('questions', models.JSONField(blank=True, help_text='[{"text": "How do I apply for leave?", "vector": [...]}]', null=True)),
                ('embedding_vector', pgvector.django.vector.VectorField(dimensions=1536, help_text='vector of this one item')),
                ('model_name', models.CharField(max_length=100)),
                ('model_version', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metadata_type', models.ForeignKey(db_column='metadata_type_id', on_delete=django.db.models.deletion.CASCADE, related_name='embeddings', to='rag.metadatatype')),
                ('segment', models.ForeignKey(db_column='segment_id', on_delete=django.db.models.deletion.CASCADE, related_name='embeddings', to='rag.knowledgesegment')),
            ],
            options={
                'db_table': 'knowledge_embeddings',
            },
        ),
        migrations.DeleteModel(
            name='SegmentEmbedding',
        ),
        migrations.DeleteModel(
            name='VideoSegment',
        ),
        migrations.DeleteModel(
            name='Video',
        ),
        migrations.AddConstraint(
            model_name='knowledgesource',
            constraint=models.UniqueConstraint(fields=('knowledge', 'language'), name='unique_knowledge_source_language'),
        ),
        migrations.AddConstraint(
            model_name='knowledgesegment',
            constraint=models.UniqueConstraint(fields=('knowledge', 'segment_index'), name='unique_knowledge_segment_index'),
        ),
        migrations.AddIndex(
            model_name='knowledgeembedding',
            index=models.Index(fields=['segment', 'metadata_type'], name='k_emb_seg_mtype_idx'),
        ),
        migrations.AddConstraint(
            model_name='knowledgeembedding',
            constraint=models.UniqueConstraint(fields=('segment', 'metadata_type', 'item_index', 'model_name', 'model_version'), name='unique_k_emb_item_model'),
        ),
    ]
