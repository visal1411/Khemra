import base64
from rest_framework import serializers
from apps.rag.models.enums import SourceType


class KnowledgeSourceInputSerializer(serializers.Serializer):
    language = serializers.CharField(max_length=10, required=True)
    file_data = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    file_url = serializers.CharField(max_length=1000, required=False, allow_blank=True, allow_null=True)
    duration_seconds = serializers.FloatField(required=False, allow_null=True)
    page_count = serializers.IntegerField(required=False, allow_null=True)

    def validate_file_data(self, value):
        if value:
            try:
                base64.b64decode(value, validate=True)
            except Exception as e:
                raise serializers.ValidationError(f"Invalid base64 encoded binary data: {e}")
        return value


class KnowledgeSegmentInputSerializer(serializers.Serializer):
    segment_index = serializers.IntegerField(min_value=0, required=True)
    title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    transcript = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    keywords = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    possible_questions = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    start_time_seconds = serializers.FloatField(required=False, allow_null=True)
    end_time_seconds = serializers.FloatField(required=False, allow_null=True)
    page_start = serializers.IntegerField(required=False, allow_null=True)
    page_end = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        start_t = data.get("start_time_seconds")
        end_t = data.get("end_time_seconds")
        if start_t is not None and end_t is not None and start_t > end_t:
            raise serializers.ValidationError({"start_time_seconds": "start_time_seconds cannot be greater than end_time_seconds"})

        page_s = data.get("page_start")
        page_e = data.get("page_end")
        if page_s is not None and page_e is not None and page_s > page_e:
            raise serializers.ValidationError({"page_start": "page_start cannot be greater than page_end"})

        return data


class KnowledgeInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=500, required=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source_type = serializers.ChoiceField(choices=SourceType.choices, required=True)
    sources = serializers.ListField(child=KnowledgeSourceInputSerializer(), required=False, default=list)
    segments = serializers.ListField(child=KnowledgeSegmentInputSerializer(), required=False)
    knowledge_segments = serializers.ListField(child=KnowledgeSegmentInputSerializer(), required=False)

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty or whitespace only.")
        return value.strip()

    def _validate_source_file_signature(self, raw_bytes, source_type, lang):
        if not raw_bytes:
            return

        if source_type == SourceType.PDF:
            if not raw_bytes.startswith(b"%PDF-"):
                raise serializers.ValidationError({
                    "sources": f"Invalid PDF file format for language '{lang}'. File header does not match PDF format ('%PDF-')."
                })

        elif source_type == SourceType.VIDEO:
            is_mp4 = len(raw_bytes) >= 8 and raw_bytes[4:8] in (b"ftyp", b"moov", b"mdat", b"wide")
            is_webm_mkv = raw_bytes.startswith(b"\x1a\x45\xdf\xa3")
            is_avi = len(raw_bytes) >= 12 and raw_bytes.startswith(b"RIFF") and raw_bytes[8:12] == b"AVI "
            is_mpeg = raw_bytes.startswith(b"\x00\x00\x01\xba") or (len(raw_bytes) > 0 and raw_bytes[0] == 0x47)
            if not (is_mp4 or is_webm_mkv or is_avi or is_mpeg):
                raise serializers.ValidationError({
                    "sources": f"Invalid video file format for language '{lang}'. File header is not a recognized video container (MP4, WebM/MKV, AVI, MPEG)."
                })

        elif source_type == SourceType.TEXT:
            try:
                raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    raw_bytes.decode("utf-16")
                except UnicodeDecodeError:
                    raise serializers.ValidationError({
                        "sources": f"Invalid text file format for language '{lang}'. Content must be valid UTF-8 or UTF-16 encoded text."
                    })

    def validate(self, data):
        # Support either segments or knowledge_segments
        segments = data.get("segments") or data.get("knowledge_segments")
        if not segments:
            raise serializers.ValidationError({"segments": "At least one segment must be provided in 'segments' or 'knowledge_segments'."})
        data["segments"] = segments

        source_type = data.get("source_type")
        sources = data.get("sources") or []

        # Check unique language per knowledge in sources and validate file binary signatures
        languages = []
        for src in sources:
            lang = src.get("language")
            languages.append(lang)
            file_str = src.get("file_data")
            if file_str:
                raw_bytes = base64.b64decode(file_str)
                self._validate_source_file_signature(raw_bytes, source_type, lang)

        if len(languages) != len(set(languages)):
            raise serializers.ValidationError({"sources": "Duplicate languages found in sources. Each source must have a unique language."})

        # Check unique segment_index
        indices = [s["segment_index"] for s in segments]
        if len(indices) != len(set(indices)):
            raise serializers.ValidationError({"segments": "Duplicate segment_index found. Each segment must have a unique segment_index."})

        return data
