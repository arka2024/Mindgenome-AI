from __future__ import annotations

import asyncio

import fitz
import pytest
from app.adapters.gemini import OCR_PDF_MAX_CONCURRENCY, gemini_adapter


@pytest.mark.asyncio
async def test_pdf_ocr_processes_pages_concurrently_in_page_order(monkeypatch):
    pdf = fitz.open()
    for _ in range(5):
        pdf.new_page()
    content = pdf.tobytes()
    pdf.close()

    active_requests = 0
    max_active_requests = 0

    async def fake_ocr_image_bytes(_content: bytes) -> str:
        nonlocal active_requests, max_active_requests
        active_requests += 1
        max_active_requests = max(max_active_requests, active_requests)
        await asyncio.sleep(0.01)
        active_requests -= 1
        return "recognized"

    monkeypatch.setattr(gemini_adapter, "ocr_image_bytes", fake_ocr_image_bytes)

    result = await gemini_adapter.ocr_pdf_bytes(content)

    assert max_active_requests == OCR_PDF_MAX_CONCURRENCY
    assert result == "\n\n".join(f"[Page {page}]\nrecognized" for page in range(1, 6))
