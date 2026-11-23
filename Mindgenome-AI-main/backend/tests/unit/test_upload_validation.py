from __future__ import annotations

import io
import zipfile
import pytest
from app.core.upload_validation import UploadValidationException, validate_and_inspect_upload


def test_valid_pdf_validation():
    dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    name, mime, size, sha = validate_and_inspect_upload("notes.pdf", dummy_pdf)
    assert name == "notes.pdf"
    assert mime == "application/pdf"
    assert size == len(dummy_pdf)
    assert len(sha) == 64


def test_valid_docx_validation():
    # Construct an in-memory DOCX zip with [Content_Types].xml
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("word/document.xml", "<w:document></w:document>")
    docx_bytes = bio.getvalue()

    name, mime, size, sha = validate_and_inspect_upload("handout.docx", docx_bytes)
    assert name == "handout.docx"
    assert "wordprocessingml" in mime
    assert size == len(docx_bytes)


def test_empty_file_rejected():
    with pytest.raises(UploadValidationException) as exc_info:
        validate_and_inspect_upload("empty.pdf", b"")
    assert exc_info.value.status_code == 422


def test_oversized_file_rejected():
    # 26 MB exceeds 25 MB limit
    large_data = b"x" * (26 * 1024 * 1024)
    with pytest.raises(UploadValidationException) as exc_info:
        validate_and_inspect_upload("big.pdf", large_data)
    assert exc_info.value.status_code == 413


def test_fake_pdf_signature_rejected():
    fake_pdf = b"NOT_A_REAL_PDF_FILE"
    with pytest.raises(UploadValidationException) as exc_info:
        validate_and_inspect_upload("fake.pdf", fake_pdf)
    assert exc_info.value.status_code == 415


def test_pdf_launch_action_rejected():
    malicious_pdf = b"%PDF-1.4\n/Launch /Action << /F (malicious.exe) >>\n%%EOF"
    with pytest.raises(UploadValidationException) as exc_info:
        validate_and_inspect_upload("exploit.pdf", malicious_pdf)
    assert exc_info.value.status_code == 415
    assert "launch" in exc_info.value.detail.lower()
