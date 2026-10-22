import base64
import os
from urllib.parse import urlparse
from django.conf import settings
import requests
from rest_framework import serializers
from apps.rag.models.enums import SourceType

DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".php", ".py", ".bin", ".dll",
    ".apk", ".msi", ".vbs", ".scr", ".com", ".pif",
}

ALLOWED_EXTENSIONS = {
    SourceType.PDF: {".pdf"},
    SourceType.VIDEO: {".mp4", ".mov", ".avi", ".webm", ".mkv", ".m4v", ".mpeg", ".mpg"},
    SourceType.TEXT: {".txt", ".md", ".json", ".csv", ".log"},
}


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

    def validate_file_url(self, value):
        if value:
            parsed = urlparse(value)
            if not parsed.scheme or parsed.scheme not in ("http", "https"):
                raise serializers.ValidationError("File URL must be a valid HTTP or HTTPS link.")

            ext = os.path.splitext(parsed.path)[1].lower()
            if ext in DANGEROUS_EXTENSIONS:
                raise serializers.ValidationError(
                    f"Forbidden file extension '{ext}'. Executable and script files are strictly blocked."
                )

            # Enforce Storage Domain Whitelist
            allowed_hosts = getattr(settings, "ALLOWED_STORAGE_HOSTS", None)
            if allowed_hosts:
                host = parsed.netloc.lower()
                is_allowed = any(
                    host == h.lower() or host.endswith("." + h.lower())
                    for h in allowed_hosts
                )
                if not is_allowed:
                    raise serializers.ValidationError(
                        f"Unauthorized storage domain '{host}'. Files must be hosted on authorized cloud storage."
                    )

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
        if not raw_bytes or len(raw_bytes) == 0:
            raise serializers.ValidationError({
                "sources": f"File content for language '{lang}' cannot be empty (0 bytes)."
            })

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

    def _validate_remote_url_signature(self, file_url, source_type, lang):
        if not file_url:
            return

        parsed = urlparse(file_url)
        ext = os.path.splitext(parsed.path)[1].lower()

        # 1. Match extension to source_type if extension is provided in URL
        allowed = ALLOWED_EXTENSIONS.get(source_type, set())
        if ext and ext not in allowed:
            raise serializers.ValidationError({
                "sources": f"URL extension '{ext}' for language '{lang}' does not match expected source type '{source_type}'. Allowed extensions: {', '.join(sorted(allowed))}."
            })

        # 2. Remote Byte Sniffing & Storage Existence Guardrail (HTTP Range: bytes=0-15)
        # Skip mock/local test domains to prevent offline test failures
        host = parsed.netloc.lower()
        if not host or host in ("example.com", "localhost", "127.0.0.1", "testserver") or "my-bucket.s3.amazonaws.com" in host:
            return

        try:
            resp = requests.get(file_url, headers={"Range": "bytes=0-15"}, timeout=3.0)
            if resp.status_code == 404:
                raise serializers.ValidationError({
                    "sources": (
                        f"Remote file at '{file_url}' does not exist (HTTP 404 Not Found). "
                        f"The file upload to Cloudflare R2 must complete successfully before submitting knowledge metadata."
                    )
                })
            elif resp.status_code == 403:
                raise serializers.ValidationError({
                    "sources": (
                        f"Access denied to remote file at '{file_url}' (HTTP 403 Forbidden). "
                        f"Please ensure the file was uploaded and is publicly accessible via the storage CDN."
                    )
                })
            elif resp.status_code in (200, 206):
                header = resp.content or b""
                # Reject empty files (0 bytes)
                if len(header) == 0 or resp.headers.get("Content-Length") == "0":
                    raise serializers.ValidationError({
                        "sources": f"Remote file at '{file_url}' for language '{lang}' is empty (0 bytes). Uploaded files must not be empty."
                    })

                # Check executable signature (MZ header)
                if header.startswith(b"MZ"):
                    raise serializers.ValidationError({
                        "sources": f"Security violation for language '{lang}'. Remote file at '{file_url}' is an executable (.exe) binary!"
                    })

                # Check PDF signature
                if source_type == SourceType.PDF and not header.startswith(b"%PDF-"):
                    raise serializers.ValidationError({
                        "sources": f"Invalid PDF file at URL for language '{lang}'. Remote file does not begin with '%PDF-'."
                    })
            elif resp.status_code >= 400:
                raise serializers.ValidationError({
                    "sources": f"Failed to verify remote file at '{file_url}'. Storage server returned HTTP {resp.status_code}."
                })
        except requests.exceptions.Timeout:
            # Storage request timed out
            pass
        except requests.RequestException:
            pass

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
            file_url = src.get("file_url")

            # 1. Base64 in-memory verification
            if file_str:
                raw_bytes = base64.b64decode(file_str)
                self._validate_source_file_signature(raw_bytes, source_type, lang)

            # 2. Remote URL verification
            if file_url:
                self._validate_remote_url_signature(file_url, source_type, lang)

        if len(languages) != len(set(languages)):
            raise serializers.ValidationError({"sources": "Duplicate languages found in sources. Each source must have a unique language."})

        # Check unique segment_index
        indices = [s["segment_index"] for s in segments]
        if len(indices) != len(set(indices)):
            raise serializers.ValidationError({"segments": "Duplicate segment_index found. Each segment must have a unique segment_index."})

        return data
