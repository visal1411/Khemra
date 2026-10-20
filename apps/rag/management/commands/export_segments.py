import json

from django.core.management.base import BaseCommand

from apps.rag.models import VideoSegment


class Command(BaseCommand):
    help = "Export all segments from the DB to a JSON file (for easy checking)."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, nargs="?", default="seed_data/exported_segments.json")

    def handle(self, *args, **options):
        data = [s.to_dict() for s in VideoSegment.objects.all()]
        with open(options["json_path"], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.stdout.write(self.style.SUCCESS(f"Exported {len(data)} segments to {options['json_path']}"))
