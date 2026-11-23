from __future__ import annotations

import pytest
from httpx import AsyncClient
from app.workers.tasks.ingestion import _async_process_document
from tests.integration.test_document_api import create_minimal_pdf


@pytest.mark.asyncio
async def test_rag_tutor_ask_grounded_and_ungrounded(client: AsyncClient):
    # 1. Register Alice
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice_rag@test.com", "display_name": "Alice RAG", "password": "Password123456!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Alice uploads and processes document
    pdf_bytes = create_minimal_pdf()
    files = {"file": ("gradient_boosting_notes.pdf", pdf_bytes, "application/pdf")}
    up = await client.post("/api/v1/documents", headers=headers, files=files)
    doc_id = up.json()["document_id"]
    job_id = up.json()["job_id"]

    # Process ingestion (extracts concepts, creates Neo4j nodes, embeds into Qdrant)
    await _async_process_document(job_id)

    # 3. Ask relevant grounded question
    tutor_resp = await client.post(
        "/api/v1/tutor/ask",
        headers=headers,
        json={"question": "What is gradient boosting and how does it use decision trees?"},
    )
    assert tutor_resp.status_code == 200
    tutor_data = tutor_resp.json()
    assert tutor_data["grounded"] is True
    assert tutor_data["confidence"] in ("high", "medium")
    assert len(tutor_data["citations"]) >= 1
    assert tutor_data["citations"][0]["document_id"] == doc_id
    assert "gradient_boosting_notes.pdf" in tutor_data["citations"][0]["filename"]

    # 4. Check chunk retrieval API
    chunk_id = tutor_data["citations"][0]["chunk_id"]
    chunk_resp = await client.get(f"/api/v1/chunks/{chunk_id}", headers=headers)
    assert chunk_resp.status_code == 200
    assert chunk_resp.json()["id"] == chunk_id
    assert len(chunk_resp.json()["passage"]) > 0

    # 5. Ask completely unrelated question (e.g. quantum crypto weather)
    ungrounded_resp = await client.post(
        "/api/v1/tutor/ask",
        headers=headers,
        json={"question": "What is the weather and quantum crypto forecast in Antarctica?"},
    )
    assert ungrounded_resp.status_code == 200
    # In vector search, completely unweighted words will either have low score or refusal
    assert "message" in ungrounded_resp.json()


@pytest.mark.asyncio
async def test_rag_cross_tenant_isolation(client: AsyncClient):
    # Register User A (Alice)
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice_sec@test.com", "display_name": "Alice Sec", "password": "Password123456!"},
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    # Register User B (Bob)
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob_sec@test.com", "display_name": "Bob Sec", "password": "Password123456!"},
    )
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # Alice uploads document
    files = {"file": ("alice_confidential.pdf", create_minimal_pdf(), "application/pdf")}
    up = await client.post("/api/v1/documents", headers=headers_a, files=files)
    await _async_process_document(up.json()["job_id"])

    # Bob asks about Alice's document -> Bob has 0 documents indexed, so Qdrant query filter must yield 0 results
    bob_tutor = await client.post(
        "/api/v1/tutor/ask",
        headers=headers_b,
        json={"question": "Gradient Boosting and Decision Trees"},
    )
    assert bob_tutor.status_code == 200
    assert bob_tutor.json()["grounded"] is False
    assert bob_tutor.json()["confidence"] == "low"
    assert len(bob_tutor.json()["citations"]) == 0
