"""Migration: resize embedding_vector from 1536 to 384 dimensions.

all-MiniLM-L6-v2 natively produces 384-dimensional vectors so we align
the PostgreSQL pgvector column to match.
"""
from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ("rag", "0003_knowledge_schema"),
    ]

    operations = [
        migrations.AlterField(
            model_name="knowledgeembedding",
            name="embedding_vector",
            field=pgvector.django.VectorField(
                dimensions=384,
                help_text="vector of this one item",
            ),
        ),
    ]
