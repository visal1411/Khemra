import json

from django.core.management.base import BaseCommand, CommandError

from apps.rag.services.SegmentIngestService import SegmentIngestService


class Command(BaseCommand):
    help = "Load video segments from a JSON file into the DB (embeds each metadata field + upserts)."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str)

    def handle(self, *args, **options):
        with open(options["json_path"], "r", encoding="utf-8") as f:
            segments = json.load(f)

        try:
            result = SegmentIngestService().upsert_many(segments)
        except ValueError as e:
            raise CommandError(str(e))

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {len(segments)} segments (created {result['created']}, updated {result['updated']})."
        ))
