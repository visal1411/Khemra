# Phase 0 Research: Cloudflare R2 Presigned Uploads

**Feature**: Cloudflare R2 Presigned Direct Upload  
**Date**: 2026-10-21  

---

## Research Question 1: How does Cloudflare R2 S3 Compatibility work with Python `boto3`?

### Decision:
Use the standard AWS SDK for Python (`boto3` and `botocore`) configured with Cloudflare R2's account endpoint URL and Signature Version 4 (`s3v4`).

### Rationale:
Cloudflare R2 implements the S3 API standard. To connect to Cloudflare R2:
- **`endpoint_url`**: `https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com`
- **`aws_access_key_id`**: Cloudflare R2 Access Key ID.
- **`aws_secret_access_key`**: Cloudflare R2 Secret Access Key.
- **`region_name`**: `"auto"` (R2 is globally distributed; `"auto"` or `"apac"` / `"us-east-1"` is accepted, but Cloudflare recommends `"auto"`).
- **Signature Version**: `Config(signature_version="s3v4")` is required because R2 strictly requires AWS Signature Version 4 for signing.

### Alternatives Considered:
- *Cloudflare API v4 Python wrapper*: Does not have direct streaming presigned URL capabilities for object storage; S3 API via `boto3` is the official and recommended way by Cloudflare.
- *Django-storages package*: Excellent for Django model `FileField`, but our RAG architecture decouples metadata from binary storage, preferring direct client uploads. Direct `boto3` gives full control over the presigned URL generation without unnecessary ORM overhead.

---

## Research Question 2: Should the Presigned URL be HTTP PUT or HTTP POST?

### Decision:
Use **HTTP `PUT`** (`ClientMethod="put_object"`).

### Rationale:
- S3 `put_object` presigned URLs allow the client to make a clean, single HTTP `PUT` request with the raw binary file as the request body (`body: file`).
- S3 `post_object` requires `multipart/form-data` with exact form field order (key, policy, signature, file), which is more complex and error-prone for frontend and mobile clients to assemble.
- Standard frontend libraries (`fetch`, `axios`, `uppy`) work seamlessly with presigned PUT URLs.

### Critical Gotcha:
When generating the presigned PUT URL with `Params={"ContentType": file_type}`, AWS SigV4 signs the `Content-Type` header. The client's HTTP PUT **MUST** send the exact same `Content-Type` header, or Cloudflare R2 will reject the request with `403 SignatureDoesNotMatch`.

---

## Research Question 3: How to test the Presigned URL service offline without live Cloudflare credentials?

### Decision:
Implement unit tests using `unittest.mock.patch` on `boto3.client`.

### Rationale:
- Constitution Principle IV states: *"Tests MUST run completely offline and finish within seconds."*
- We must not require actual Cloudflare credentials or network connectivity during `python manage.py test` runs or Docker CI/CD pipelines.
- Mocking `s3_client.generate_presigned_url` enables full testing of:
  1. Input validation & query parameter parsing.
  2. Dangerous extension blocking.
  3. Key generation format and UUID uniqueness.
  4. URL construction and JSON response format.
  5. Error handling when `boto3` raises `ClientError`.
