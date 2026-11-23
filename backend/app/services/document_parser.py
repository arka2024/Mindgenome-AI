from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Any
import docx
from pypdf import PdfReader
from app.core.logging import logger

try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    tokenizer = None


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (or fallback word estimation)."""
    if tokenizer is not None:
        return len(tokenizer.encode(text))
    # Approximation: 1 token ~ 0.75 words
    words = len(text.split())
    return max(1, int(words * 1.33))


@dataclass
class ExtractedChapter:
    title: str
    ordinal: int
    start_page: int
    end_page: int


@dataclass
class ExtractedChunk:
    ordinal: int
    page_start: int
    page_end: int
    heading_path: str | None
    body: str
    token_count: int


@dataclass
class ParsedDocumentResult:
    page_count: int
    is_low_text: bool
    low_text_warning: str | None
    chapters: list[ExtractedChapter]
    chunks: list[ExtractedChunk]


class DocumentParser:
    def __init__(self, target_tokens: int = 512, overlap_tokens: int = 64) -> None:
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens

    def clean_text(self, text: str) -> str:
        """Strip non-printable characters and normalize whitespace."""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    def parse_pdf(self, content: bytes) -> ParsedDocumentResult:
        reader = PdfReader(io.BytesIO(content))
        page_count = len(reader.pages)
        pages_text: list[tuple[int, str]] = []

        total_chars = 0
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            raw_text = page.extract_text() or ""
            cleaned = self.clean_text(raw_text)
            total_chars += len(cleaned)
            if cleaned:
                pages_text.append((page_num, cleaned))

        # Check for scanned / low-text PDF
        is_low_text = False
        low_text_warning = None
        if page_count > 0 and (total_chars / page_count) < 50:
            is_low_text = True
            low_text_warning = "Document appears to be scanned or contains very little extractable text."

        # Chapters from outlines/bookmarks if available
        chapters: list[ExtractedChapter] = []
        try:
            outline = reader.outline
            ordinal = 0
            if outline:
                for item in outline:
                    if hasattr(item, "title") and hasattr(item, "page"):
                        try:
                            page_dest = reader.get_destination_page_number(item) + 1
                            chapters.append(
                                ExtractedChapter(
                                    title=str(item.title).strip(),
                                    ordinal=ordinal,
                                    start_page=page_dest,
                                    end_page=page_count,
                                )
                            )
                            ordinal += 1
                        except Exception:
                            pass
        except Exception:
            pass

        # If no outlines found, create default chapter
        if not chapters:
            chapters = [
                ExtractedChapter(
                    title="Main Content",
                    ordinal=0,
                    start_page=1,
                    end_page=max(1, page_count),
                )
            ]
        else:
            # Fix end_page for successive chapters
            for idx in range(len(chapters) - 1):
                chapters[idx].end_page = max(chapters[idx].start_page, chapters[idx + 1].start_page - 1)

        # Chunking
        chunks = self._chunk_pages(pages_text)

        return ParsedDocumentResult(
            page_count=page_count,
            is_low_text=is_low_text,
            low_text_warning=low_text_warning,
            chapters=chapters,
            chunks=chunks,
        )

    def parse_docx(self, content: bytes) -> ParsedDocumentResult:
        doc = docx.Document(io.BytesIO(content))
        paragraphs = []
        chapters: list[ExtractedChapter] = []
        current_heading = "Overview"
        ordinal = 0

        for p in doc.paragraphs:
            text = self.clean_text(p.text)
            if not text:
                continue

            if p.style and p.style.name and p.style.name.startswith("Heading"):
                current_heading = text
                chapters.append(
                    ExtractedChapter(
                        title=text,
                        ordinal=ordinal,
                        start_page=1,
                        end_page=1,
                    )
                )
                ordinal += 1

            paragraphs.append((current_heading, text))

        if not chapters:
            chapters = [
                ExtractedChapter(
                    title="Document Content",
                    ordinal=0,
                    start_page=1,
                    end_page=1,
                )
            ]

        # Estimated page count
        total_text = " ".join(t[1] for t in paragraphs)
        page_count = max(1, len(total_text) // 2500)

        chunks = self._chunk_paragraphs(paragraphs)

        return ParsedDocumentResult(
            page_count=page_count,
            is_low_text=len(total_text) < 50,
            low_text_warning="Very little text found in DOCX document." if len(total_text) < 50 else None,
            chapters=chapters,
            chunks=chunks,
        )

    def _chunk_pages(self, pages: list[tuple[int, str]]) -> list[ExtractedChunk]:
        chunks: list[ExtractedChunk] = []
        chunk_ordinal = 0

        current_body_parts: list[str] = []
        current_token_count = 0
        chunk_start_page = pages[0][0] if pages else 1
        chunk_end_page = chunk_start_page

        for page_num, page_text in pages:
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]

            for p in paragraphs:
                p_tokens = count_tokens(p)

                if current_token_count + p_tokens > self.target_tokens and current_body_parts:
                    # Finalize current chunk
                    body = "\n\n".join(current_body_parts)
                    chunks.append(
                        ExtractedChunk(
                            ordinal=chunk_ordinal,
                            page_start=chunk_start_page,
                            page_end=chunk_end_page,
                            heading_path=None,
                            body=body,
                            token_count=current_token_count,
                        )
                    )
                    chunk_ordinal += 1

                    # Retain overlap from end of previous chunk if possible
                    if self.overlap_tokens > 0 and len(current_body_parts) > 1:
                        current_body_parts = [current_body_parts[-1]]
                        current_token_count = count_tokens(current_body_parts[0])
                    else:
                        current_body_parts = []
                        current_token_count = 0

                    chunk_start_page = page_num

                current_body_parts.append(p)
                current_token_count += p_tokens
                chunk_end_page = page_num

        if current_body_parts:
            body = "\n\n".join(current_body_parts)
            chunks.append(
                ExtractedChunk(
                    ordinal=chunk_ordinal,
                    page_start=chunk_start_page,
                    page_end=chunk_end_page,
                    heading_path=None,
                    body=body,
                    token_count=current_token_count,
                )
            )

        return chunks

    def _chunk_paragraphs(self, paragraphs: list[tuple[str, str]]) -> list[ExtractedChunk]:
        chunks: list[ExtractedChunk] = []
        chunk_ordinal = 0

        current_parts: list[str] = []
        current_token_count = 0
        current_heading: str | None = None

        for heading, text in paragraphs:
            p_tokens = count_tokens(text)

            if current_token_count + p_tokens > self.target_tokens and current_parts:
                chunks.append(
                    ExtractedChunk(
                        ordinal=chunk_ordinal,
                        page_start=1,
                        page_end=1,
                        heading_path=current_heading,
                        body="\n\n".join(current_parts),
                        token_count=current_token_count,
                    )
                )
                chunk_ordinal += 1
                current_parts = []
                current_token_count = 0

            current_heading = heading
            current_parts.append(text)
            current_token_count += p_tokens

        if current_parts:
            chunks.append(
                ExtractedChunk(
                    ordinal=chunk_ordinal,
                    page_start=1,
                    page_end=1,
                    heading_path=current_heading,
                    body="\n\n".join(current_parts),
                    token_count=current_token_count,
                )
            )

        return chunks


document_parser = DocumentParser()
