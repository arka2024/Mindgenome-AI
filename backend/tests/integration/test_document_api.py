from __future__ import annotations

import io
import zipfile
import pytest
from httpx import AsyncClient
from app.workers.tasks.ingestion import _async_process_document


def create_minimal_pdf() -> bytes:
    """Generate a valid minimal single-page PDF with text."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 53 >> stream\n"
        b"BT /F1 12 Tf 72 712 Td (Gradient Boosting and Decision Trees) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"0000000117 00000 n \n"
        b"0000000256 00000 n \n"
        b"0000000360 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n437\n%%EOF"
    )


@pytest.mark.asyncio
async def test_document_upload_and_ingestion_flow(client: AsyncClient):
    # 1. Register User A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@institution.edu", "display_name": "Alice", "password": "Password123456!"},
    )
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Upload valid PDF
    pdf_bytes = create_minimal_pdf()
    files = {"file": ("gradient_boosting.pdf", pdf_bytes, "application/pdf")}
    upload_resp = await client.post(
        "/api/v1/documents",
        headers=headers_a,
        files=files,
    )
    assert upload_resp.status_code == 202
    data = upload_resp.json()
    assert "document_id" in data
    assert "job_id" in data
    assert data["status"] == "queued"

    doc_id = data["document_id"]
    job_id = data["job_id"]

    # 3. Check ingestion job status
    job_resp = await client.get(f"/api/v1/ingestion-jobs/{job_id}", headers=headers_a)
    assert job_resp.status_code == 200
    assert job_resp.json()["document_id"] == doc_id
    assert job_resp.json()["status"] in ("queued", "ready", "parsing")

    # 4. Process document pipeline
    await _async_process_document(job_id)

    # 5. Check completed job status
    job_after = await client.get(f"/api/v1/ingestion-jobs/{job_id}", headers=headers_a)
    assert job_after.status_code == 200
    assert job_after.json()["status"] == "ready"
    assert job_after.json()["progress_pct"] == 100

    # 6. Fetch single document
    doc_resp = await client.get(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert doc_resp.status_code == 200
    doc_data = doc_resp.json()
    assert doc_data["id"] == doc_id
    assert doc_data["filename"] == "gradient_boosting.pdf"
    assert doc_data["status"] == "ready"
    assert len(doc_data["chapters"]) >= 1

    # 7. List documents
    list_resp = await client.get("/api/v1/documents", headers=headers_a)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == doc_id for d in list_data["items"])


@pytest.mark.asyncio
async def test_document_tenant_isolation(client: AsyncClient):
    # Register Alice (User A)
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice_iso@institution.edu", "display_name": "Alice", "password": "Password123456!"},
    )
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register Bob (User B)
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob_iso@institution.edu", "display_name": "Bob", "password": "Password123456!"},
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Alice uploads a document
    pdf_bytes = create_minimal_pdf()
    files = {"file": ("alice_doc.pdf", pdf_bytes, "application/pdf")}
    upload_resp = await client.post("/api/v1/documents", headers=headers_a, files=files)
    assert upload_resp.status_code == 202
    alice_doc_id = upload_resp.json()["document_id"]
    alice_job_id = upload_resp.json()["job_id"]

    # Bob attempts to GET Alice's document -> must be 404 Not Found!
    bob_get_doc = await client.get(f"/api/v1/documents/{alice_doc_id}", headers=headers_b)
    assert bob_get_doc.status_code == 404

    # Bob attempts to GET Alice's ingestion job -> must be 404 Not Found!
    bob_get_job = await client.get(f"/api/v1/ingestion-jobs/{alice_job_id}", headers=headers_b)
    assert bob_get_job.status_code == 404

    # Bob attempts to DELETE Alice's document -> must be 404 Not Found!
    bob_del_doc = await client.delete(f"/api/v1/documents/{alice_doc_id}", headers=headers_b)
    assert bob_del_doc.status_code == 404

    # Bob's document list must be empty
    bob_list = await client.get("/api/v1/documents", headers=headers_b)
    assert bob_list.status_code == 200
    assert bob_list.json()["total"] == 0


@pytest.mark.asyncio
async def test_document_reprocess_and_deletion(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "charlie@test.com", "display_name": "Charlie", "password": "Password123456!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # Upload
    files = {"file": ("charlie_doc.pdf", create_minimal_pdf(), "application/pdf")}
    up = await client.post("/api/v1/documents", headers=headers, files=files)
    doc_id = up.json()["document_id"]

    # Reprocess
    reprocess = await client.post(f"/api/v1/documents/{doc_id}/reprocess", headers=headers)
    assert reprocess.status_code == 200
    assert reprocess.json()["status"] == "queued"

    # Delete
    del_resp = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify deleted
    get_after = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_after.status_code == 404
