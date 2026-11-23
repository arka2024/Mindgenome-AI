from __future__ import annotations

import pytest
from app.services.document_parser import DocumentParser, count_tokens


def test_token_counter():
    text = "Machine learning builds models from empirical data."
    tokens = count_tokens(text)
    assert tokens >= 6


def test_clean_text():
    parser = DocumentParser()
    raw = "Hello   world!\n\n\n\nThis  is a test \t with whitespace."
    cleaned = parser.clean_text(raw)
    assert "  " not in cleaned
    assert "\n\n\n" not in cleaned
    assert cleaned.startswith("Hello world!")


def test_chunking_token_boundaries():
    parser = DocumentParser(target_tokens=30, overlap_tokens=5)
    pages = [
        (1, "Paragraph one about gradient boosting and decision trees in machine learning.\n\nParagraph two describes bagging, variance reduction, and random forests."),
        (2, "Paragraph three discusses regularization, learning rate shrinkage, and early stopping criteria in iterative boosting algorithms."),
    ]
    chunks = parser._chunk_pages(pages)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.token_count > 0
        assert chunk.page_start >= 1
        assert chunk.page_end >= chunk.page_start
        assert len(chunk.body) > 0
