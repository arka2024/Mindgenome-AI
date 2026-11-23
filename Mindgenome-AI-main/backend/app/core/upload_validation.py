from __future__ import annotations

import hashlib
import io
import zipfile
from app.core.config import settings
from app.core.exceptions import ProblemException

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"


class UploadValidationException(ProblemException):
    def __init__(self, detail: str, status_code: int = 415) -> None:
        super().__init__(
            status_code=status_code,
            title="Upload rejected",
            detail=detail,
            problem_type="upload-rejected",
        )


def validate_and_inspect_upload(
    filename: str,
    content: bytes,
    declared_content_type: str | None = None,
) -> tuple[str, str, int, str]:
    """
    Validate uploaded file content against size, extension, and magic bytes.
    Returns (normalized_filename, verified_content_type, byte_size, sha256_hex).
    """
    byte_size = len(content)

    # 1. Empty file check
    if byte_size == 0:
        raise UploadValidationException(detail="Uploaded file is empty (0 bytes).", status_code=422)

    # 2. Size limit check (25 MB max)
    if byte_size > settings.UPLOAD_MAX_BYTES:
        raise UploadValidationException(
            detail=f"File exceeds the maximum allowed size of {settings.UPLOAD_MAX_BYTES // (1024 * 1024)} MB.",
            status_code=413,
        )

    # 3. Extension check
    lower_name = filename.lower()
    allowed_extensions = (".pdf", ".docx", ".txt", ".md", ".jpg", ".jpeg", ".png")
    if not lower_name.endswith(allowed_extensions):
        raise UploadValidationException(
            detail="Unsupported file extension. PDF, DOCX, text, Markdown, JPG, JPEG, and PNG files are permitted.",
            status_code=415,
        )

    # 4. Magic bytes & content inspection
    if lower_name.endswith(".pdf"):
        if not content.startswith(PDF_MAGIC):
            raise UploadValidationException(
                detail="File signature does not match a valid PDF document.",
                status_code=415,
            )
        verified_type = "application/pdf"

        # Security inspection: scan for dangerous PDF launch/JavaScript actions
        lower_content = content[:100000].lower() + content[-50000:].lower()
        if b"/launch" in lower_content:
            raise UploadValidationException(
                detail="PDF rejected: contains potentially hazardous /Launch action.",
                status_code=415,
            )

    elif lower_name.endswith(".docx"):
        if not content.startswith(ZIP_MAGIC):
            raise UploadValidationException(
                detail="File signature does not match a valid DOCX document.",
                status_code=415,
            )
        # Verify it's a valid openxml zip package containing [Content_Types].xml
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                namelist = zf.namelist()
                if "[Content_Types].xml" not in namelist:
                    raise UploadValidationException(
                        detail="DOCX archive missing [Content_Types].xml specification.",
                        status_code=415,
                    )
        except zipfile.BadZipFile:
            raise UploadValidationException(
                detail="Corrupted or malformed DOCX package.",
                status_code=415,
            )
        verified_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif lower_name.endswith(".txt"):
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise UploadValidationException(
                detail="Text document must be valid UTF-8 encoded text.",
                status_code=415,
            )
        verified_type = "text/plain"
    elif lower_name.endswith((".jpg", ".jpeg", ".png")):
        try:
            from PIL import Image

            with Image.open(io.BytesIO(content)) as image:
                image.verify()
        except Exception:
            raise UploadValidationException(
                detail="Corrupted or malformed image document.",
                status_code=415,
            )
        verified_type = "image/png" if lower_name.endswith(".png") else "image/jpeg"
    elif lower_name.endswith(".md"):
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise UploadValidationException(
                detail="Markdown document must be valid UTF-8 encoded text.",
                status_code=415,
            )
        verified_type = "text/markdown"
    else:
        raise UploadValidationException(detail="Unsupported file format.", status_code=415)

    # 5. Compute SHA-256 digest
    sha256_hash = hashlib.sha256(content).hexdigest()

    return filename, verified_type, byte_size, sha256_hash
