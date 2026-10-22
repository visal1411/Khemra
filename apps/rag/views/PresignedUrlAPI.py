import os
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.services.StorageService import StorageService

DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".php", ".py", ".bin", ".dll",
    ".apk", ".msi", ".vbs", ".scr", ".com", ".pif",
}


class PresignedUrlAPI(APIView):
    """
    GET /api/rag/storage/presigned-url/?filename=guide.pdf&file_type=application/pdf
    Generates a pre-signed Cloudflare R2 / S3 PUT URL for direct client upload.
    """

    def get(self, request):
        filename = request.query_params.get("filename")
        file_type = request.query_params.get("file_type")
        folder = request.query_params.get("folder", "documents")

        if not filename or not filename.strip() or not file_type or not file_type.strip():
            return Response(
                {"error": "Both 'filename' and 'file_type' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = filename.strip()
        file_type = file_type.strip()

        # Reject empty files if file_size is provided by client
        file_size = request.query_params.get("file_size")
        if file_size is not None:
            try:
                size_int = int(file_size)
                if size_int <= 0:
                    return Response(
                        {"error": "File size must be greater than 0 bytes. Empty files cannot be uploaded."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                return Response(
                    {"error": "Query parameter 'file_size' must be a valid integer number of bytes."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Check for dangerous executable and script extensions
        _, ext = os.path.splitext(filename)
        clean_ext = ext.lower()

        if not clean_ext:
            return Response(
                {"error": "Filename must include a valid file extension."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if clean_ext in DANGEROUS_EXTENSIONS:
            return Response(
                {"error": f"Forbidden file extension '{clean_ext}'. Executable and script files are strictly blocked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            storage_service = StorageService()
            data = storage_service.generate_presigned_upload_url(
                filename=filename,
                content_type=file_type,
                folder=folder,
            )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to generate presigned upload URL: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
