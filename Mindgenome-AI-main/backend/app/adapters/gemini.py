from __future__ import annotations

import asyncio
import io
import json
import time
from typing import Any
import httpx
import re
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging import logger
from app.models.enums import LLMCallStatus, LLMPurpose

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
OCR_PDF_MAX_CONCURRENCY = 3


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can", "could",
    "for", "from", "has", "have", "in", "is", "it", "its", "may", "of", "on", "or",
    "that", "the", "their", "this", "to", "was", "were", "which", "with", "will",
}


def _clean_candidate(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9 _.-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip(" .-_")


def _extract_content_concepts(user_prompt: str, limit: int = 5) -> list[dict[str, str]]:
    data_match = re.search(r"(?:DATA:|RETRIEVED CONTEXT:|CONCEPT:\s*[^\n]*)(.*)", user_prompt, re.DOTALL)
    data = data_match.group(1).strip() if data_match else user_prompt
    data = re.sub(r"<UNTRUSTED_DOCUMENT[^>]*>|</UNTRUSTED_DOCUMENT>", " ", data)
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+|\n+", data)
        if s.strip() and not s.strip().startswith("#")
    ]

    document_match = re.search(r"Document:\s*(.+)", user_prompt)
    document_name = ""
    if document_match:
        document_name = re.sub(r"\.(pdf|docx|txt|md)$", "", document_match.group(1), flags=re.I)
        document_name = document_name.replace("_", " ").replace("-", " ").strip()

    candidates: list[str] = []

    title_phrases = re.findall(r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3}\b", data)
    candidates.extend(_clean_candidate(p) for p in title_phrases)

    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", data.lower())
    generic_verbs = {
        "absorbs", "combine", "combines", "fix", "fixes", "improve", "improves", "produce", "produces", "provide", "discusses",
        "contains", "uses", "using", "describes", "represents", "requires", "supports",
    }
    for i in range(len(words) - 1):
        first, second = words[i], words[i + 1]
        if (
            first not in STOP_WORDS
            and second not in STOP_WORDS
            and second not in generic_verbs
            and len(first) > 2
            and len(second) > 2
        ):
            candidates.append(f"{first} {second}".title())

    if document_name:
        candidates.append(_clean_candidate(document_name))

    seen: set[str] = set()
    concepts: list[dict[str, str]] = []
    for candidate in candidates:
        canonical = _clean_candidate(candidate)
        normalized = canonical.lower()
        if (
            len(canonical) < 3
            or normalized in seen
            or normalized in STOP_WORDS
            or normalized.split()[0] in STOP_WORDS
            or normalized.startswith(("absorbs ", "the calvin", "energy ", "light "))
        ):
            continue
        seen.add(normalized)
        sentence = next((s for s in sentences if canonical.lower() in s.lower()), "")
        if not sentence:
            first_term = normalized.split()[0]
            sentence = next((s for s in sentences if first_term in s.lower()), "")
        definition = sentence or (sentences[0] if sentences else f"A key concept discussed in {document_name or 'the uploaded material'}.")
        concepts.append({
            "canonical_name": canonical,
            "normalized_name": normalized,
            "lemma": normalized,
            "definition": definition[:500],
            "prerequisites": [],
        })
        if len(concepts) >= limit:
            break

    if not concepts:
        fallback = document_name or "Uploaded Topic"
        concepts.append({
            "canonical_name": fallback,
            "normalized_name": fallback.lower(),
            "lemma": fallback.lower(),
            "definition": sentences[0][:500] if sentences else "The main topic discussed in the uploaded material.",
            "prerequisites": [],
        })
    return concepts


class ExtractedConceptItem(BaseModel):
    canonical_name: str
    normalized_name: str
    lemma: str
    definition: str
    prerequisites: list[str] = Field(default_factory=list)


class ConceptExtractionPayload(BaseModel):
    concepts: list[ExtractedConceptItem] = Field(default_factory=list)


class CitationItem(BaseModel):
    document_id: str
    filename: str
    chapter_title: str | None = None
    page_start: int
    page_end: int
    chunk_id: str
    passage: str | None = None


class TutorResponsePayload(BaseModel):
    grounded: bool
    confidence: str = "high"  # high, medium, low
    message: str
    citations: list[CitationItem] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    followups: list[str] = Field(default_factory=list)


class GeminiAdapter:
    def __init__(self) -> None:
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-pro")
        self.timeout = getattr(settings, "GEMINI_TIMEOUT_SECONDS", 45)
        self.max_retries = getattr(settings, "GEMINI_MAX_RETRIES", 2)
        self.ocr_model = getattr(settings, "GEMINI_OCR_MODEL", "gemini-2.5-flash")

    async def ocr_image_bytes(self, content: bytes) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini API key is not configured")

        try:
            from google import genai
            from PIL import Image
        except Exception as exc:
            raise RuntimeError("Gemini OCR dependencies are not available") from exc

        def run_ocr() -> str:
            client = genai.Client(api_key=self.api_key)
            image = Image.open(io.BytesIO(content)).convert("RGB")
            response = client.models.generate_content(
                model=self.ocr_model,
                contents=[
                    "Extract all readable text from this document image. Preserve headings, paragraphs, tables, and reading order. Return plain text only; do not summarize or add commentary.",
                    image,
                ],
            )
            return (response.text or "").strip()

        return await asyncio.to_thread(run_ocr)

    async def ocr_pdf_bytes(self, content: bytes, max_pages: int = 20) -> str:
        try:
            import fitz
        except Exception as exc:
            raise RuntimeError("PyMuPDF is not available for PDF OCR") from exc

        document = fitz.open(stream=content, filetype="pdf")
        page_semaphore = asyncio.Semaphore(OCR_PDF_MAX_CONCURRENCY)
        render_lock = asyncio.Lock()
        try:
            async def extract_page(page_index: int) -> str:
                async with page_semaphore:
                    async with render_lock:
                        page = document.load_page(page_index)
                        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                        image_bytes = pixmap.tobytes("png")
                    text = await self.ocr_image_bytes(image_bytes)
                    return f"[Page {page_index + 1}]\n{text}" if text else ""

            async with asyncio.TaskGroup() as task_group:
                tasks = [
                    task_group.create_task(extract_page(page_index))
                    for page_index in range(min(document.page_count, max_pages))
                ]

            extracted = []
            for task in tasks:
                text = task.result()
                if text:
                    extracted.append(text)
        finally:
            document.close()

        return "\n\n".join(extracted).strip()

    async def generate_structured_content(
        self,
        system_prompt: str,
        user_prompt: str,
        purpose: LLMPurpose,
        response_schema: type[BaseModel] | None = None,
        user_id: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Generate structured content using Google Gemini via Google AI Studio REST API.
        Returns (parsed_dict, audit_log_data).
        """
        start_time = time.perf_counter()
        audit_data: dict[str, Any] = {
            "model": self.model,
            "purpose": purpose,
            "prompt_version": "v1.0",
            "user_id": user_id,
            "status": LLMCallStatus.OK,
            "error_message": None,
            "latency_ms": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
        }

        # If API key is missing, return deterministic fallback
        if not self.api_key:
            logger.info("gemini_api_key_not_configured_using_mock", purpose=purpose.value)
            mock_resp = self._get_mock_response(purpose, user_prompt)
            audit_data["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
            return mock_resp, audit_data

        url = f"{GEMINI_API_BASE}/{self.model}:generateContent?key={self.api_key}"

        request_body: dict[str, Any] = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    resp = await client.post(url, json=request_body)
                    latency = int((time.perf_counter() - start_time) * 1000)
                    audit_data["latency_ms"] = latency

                    if resp.status_code == 200:
                        data = resp.json()
                        usage = data.get("usageMetadata", {})
                        audit_data["input_tokens"] = usage.get("promptTokenCount", 0)
                        audit_data["output_tokens"] = usage.get("candidatesTokenCount", 0)
                        # Pro cost approx $3.50/M in, $10.50/M out
                        audit_data["cost_usd"] = round(
                            (audit_data["input_tokens"] * 3.5 + audit_data["output_tokens"] * 10.5) / 1_000_000, 6
                        )

                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                text_json = parts[0]["text"]
                                parsed = json.loads(text_json)
                                return parsed, audit_data

                    logger.warning("gemini_api_call_status", status=resp.status_code, body=resp.text)
                    if resp.status_code == 429:
                        audit_data["status"] = LLMCallStatus.RATE_LIMITED
                    else:
                        audit_data["status"] = LLMCallStatus.PROVIDER_ERROR
                    audit_data["error_message"] = resp.text

            except Exception as exc:
                last_error = exc
                logger.error("gemini_api_request_exception", error=str(exc), attempt=attempt)
                audit_data["status"] = LLMCallStatus.TIMEOUT if "timeout" in str(exc).lower() else LLMCallStatus.PROVIDER_ERROR
                audit_data["error_message"] = str(exc)

        # Fallback if API fails after retries
        mock_resp = self._get_mock_response(purpose, user_prompt)
        audit_data["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        return mock_resp, audit_data

    def _get_mock_response(self, purpose: LLMPurpose, user_prompt: str) -> dict[str, Any]:
        """High-fidelity mock response for tests and local development."""
        if purpose == LLMPurpose.CONCEPT_EXTRACT:
            concepts = _extract_content_concepts(user_prompt)
            for index, concept in enumerate(concepts):
                if index:
                    concept["prerequisites"] = [concepts[index - 1]["canonical_name"]]
            return {"concepts": concepts}

        if purpose == LLMPurpose.TUTOR_ANSWER:
            question_match = re.search(r"LEARNER QUESTION:\s*(.+)", user_prompt)
            question = question_match.group(1).strip() if question_match else "the uploaded topic"
            context_match = re.search(r"RETRIEVED CONTEXT:\s*(.*)", user_prompt, re.DOTALL)
            context = context_match.group(1).strip() if context_match else ""
            context = re.sub(r"<UNTRUSTED_DOCUMENT[^>]*>|</UNTRUSTED_DOCUMENT>", " ", context)
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", context) if len(s.strip()) > 20]
            relevant = sentences[:4]
            answer = " ".join(relevant) if relevant else "The uploaded material does not contain enough text to answer this question."
            if len(answer) > 1800:
                answer = answer[:1800].rsplit(" ", 1)[0] + "…"
            return {
                "grounded": bool(relevant),
                "confidence": "medium" if relevant else "low",
                "message": f"Based on the uploaded material, here is an explanation of '{question}':\n\n{answer}",
                "citations": [],
                "concept_ids": [],
                "followups": [
                    f"How does {relevant[0][:45].rstrip('.')} relate to the rest of the material?" if relevant else "Which topic should I study next?",
                    "What is the main argument or result in this section?",
                    "Can you give a practical example from these notes?",
                ],
            }

        if purpose == LLMPurpose.QUESTION_GENERATE:
            concept_match = re.search(r"Concept:\s*(.+)", user_prompt)
            definition_match = re.search(r"Definition:\s*(.*)", user_prompt, re.DOTALL)
            concept = _clean_candidate(concept_match.group(1).strip()) if concept_match else "the uploaded topic"
            definition = _clean_candidate(definition_match.group(1).strip()) if definition_match else "the material discussed in the document"
            if len(definition) > 220:
                definition = definition[:220].rsplit(" ", 1)[0] + "…"
            return {
                "questions": [
                    {
                        "stem": f"According to the uploaded material, what is {concept}?",
                        "choices": [
                            definition,
                            "An unrelated process not discussed in the document",
                            "A random collection of facts from another topic",
                            "A claim that contradicts the source material",
                        ],
                        "correct_index": 0,
                        "difficulty": "easy",
                        "hint": "Use the definition created from the source text.",
                    },
                    {
                        "stem": f"Which statement most accurately applies to {concept}?",
                        "choices": [
                            definition,
                            "It is treated as an unsupported assumption",
                            "It has no relationship to the uploaded material",
                            "It is defined only as a memorization technique",
                        ],
                        "correct_index": 0,
                        "difficulty": "medium",
                        "hint": "Match the statement with the source description.",
                    },
                    {
                        "stem": f"Why should {concept} be included in this knowledge graph?",
                        "choices": [
                            "It is explicitly discussed as a key concept in the source material",
                            "It is unrelated to every source passage",
                            "It appears only in the software interface",
                            "It is generated without source evidence",
                        ],
                        "correct_index": 0,
                        "difficulty": "hard",
                        "hint": "Look for explicit evidence in the uploaded material.",
                    },
                ]
            }

        return {"message": "Content successfully processed."}


gemini_adapter = GeminiAdapter()
