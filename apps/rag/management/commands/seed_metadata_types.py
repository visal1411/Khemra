from django.core.management.base import BaseCommand
from apps.rag.models import MetadataType

# Names must match ContentType values (keyword/question/topic/summary)
# and ScoreCombiner.DEFAULT_WEIGHTS keys
DEFAULT_METADATA_TYPES = [
    ("keyword",  0.20),
    ("question", 0.35),
    ("topic",    0.20),
    ("summary",  0.25),
]


class Command(BaseCommand):
    help = "Seed default MetadataType records (keyword, question, topic, summary) into database"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for name, weight in DEFAULT_METADATA_TYPES:
            obj, created = MetadataType.objects.get_or_create(
                name=name,
                defaults={"weight": weight, "is_active": True},
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created MetadataType '{name}' (weight={weight})"))
            else:
                updated_count += 1
                self.stdout.write(f"MetadataType '{name}' already exists (weight={obj.weight})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded metadata types: {created_count} created, {updated_count} existing."
            )
        )
