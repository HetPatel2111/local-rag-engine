"""Gemini 2.5 Flash answer generation."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from functools import lru_cache
import re
from time import perf_counter, sleep

from src.utils.env import getenv

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
DEFAULT_TIMEOUT_MS = 30_000
DEFAULT_MAX_OUTPUT_TOKENS = 512
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SEC = 2.0
REFUSAL_MESSAGE = "I don't know based on the indexed documents."
_TERMINAL_PUNCTUATION = re.compile(r"""[.!?]["')\]]?$""")

SYSTEM_INSTRUCTION = """
You are a retrieval-based assistant.

Answer ONLY using the provided context.

Rules:

- Do not invent facts.
- If context is insufficient:
  say:
  "I don't know based on the indexed documents."
- Do not use external knowledge.
- Prefer concise answers.
- Maximum:
  150 words.
- Cite sources.
- Ignore marketing language.
- Ignore testimonials.
- Ignore announcements.
- Ignore duplicated text.
""".strip()


@dataclass(frozen=True)
class GenerationResult:
    """Metadata returned by the Gemini generation layer."""

    answer: str
    model: str
    attempts: int
    latency_ms: float
    token_count: int
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = ""
    response_length: int = 0


def _build_prompt(query: str, retrieved_context: str) -> str:
    """Assemble the user prompt with the required prompt contract."""
    return f"Context:\n{retrieved_context}\n\nQuestion:\n{query}\n\nAnswer:"


@lru_cache(maxsize=1)
def _build_client():
    """Create a cached Gemini client using a locally loaded API key."""
    from google import genai
    from google.genai import types

    api_key = getenv("GOOGLE_API_KEY") or getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Set it in your local .env file before running generation."
        )

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=int(getenv("GEMINI_TIMEOUT_MS") or DEFAULT_TIMEOUT_MS),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def _count_tokens(client, prompt: str) -> int:
    """Best-effort token counting for logging and evaluation."""
    try:
        response = client.models.count_tokens(model=MODEL_NAME, contents=prompt)
        return int(getattr(response, "total_tokens", 0) or 0)
    except Exception:  # pragma: no cover - best effort only
        return max(1, len(prompt.split()))


def _stringify_finish_reason(value: object) -> str:
    """Convert a Gemini finish reason into a stable string."""
    if value is None:
        return ""

    name = getattr(value, "name", None)
    if isinstance(name, str) and name:
        return name

    raw_value = getattr(value, "value", None)
    if isinstance(raw_value, str) and raw_value:
        return raw_value

    return str(value)


def _extract_response_text(response: object) -> str:
    """Return full generated text, falling back to candidate parts when needed."""
    text = getattr(response, "text", "") or ""
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    parts: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", "")
            if isinstance(part_text, str) and part_text.strip():
                parts.append(part_text.strip())

    return "".join(parts).strip()


def _response_metrics(response: object, prompt_tokens: int, fallback_output_tokens: int) -> tuple[int, int, str]:
    """Extract token and finish metadata from a Gemini response."""
    usage_metadata = getattr(response, "usage_metadata", None)
    input_tokens = int(getattr(usage_metadata, "prompt_token_count", 0) or prompt_tokens or 0)
    output_tokens = int(getattr(usage_metadata, "candidates_token_count", 0) or fallback_output_tokens or 0)

    candidates = getattr(response, "candidates", None) or []
    finish_reason = ""
    if candidates:
        finish_reason = _stringify_finish_reason(getattr(candidates[0], "finish_reason", ""))

    return input_tokens, output_tokens, finish_reason


def _is_complete_answer(answer: str) -> bool:
    """Return True when the answer appears to end at a sentence boundary."""
    cleaned = answer.strip()
    if not cleaned:
        return False
    return bool(_TERMINAL_PUNCTUATION.search(cleaned))


def _generate_with_tokens(query: str, retrieved_context: str, max_output_tokens: int) -> GenerationResult:
    """Generate a grounded answer with the requested output token budget."""
    from google.genai import types

    client = _build_client()
    prompt = _build_prompt(query, retrieved_context)
    prompt_tokens = _count_tokens(client, prompt)
    started = perf_counter()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
            max_output_tokens=max_output_tokens,
            candidate_count=1,
        ),
    )
    latency_ms = (perf_counter() - started) * 1000.0
    answer = _extract_response_text(response) or REFUSAL_MESSAGE
    input_tokens, output_tokens, finish_reason = _response_metrics(
        response,
        prompt_tokens=prompt_tokens,
        fallback_output_tokens=max(1, len(answer.split())),
    )

    logger.info(
        "generation success model=%s input_tokens=%s output_tokens=%s finish_reason=%s response_length=%s latency_ms=%.2f",
        MODEL_NAME,
        input_tokens,
        output_tokens,
        finish_reason or "UNKNOWN",
        len(answer),
        latency_ms,
    )

    return GenerationResult(
        answer=answer,
        model=MODEL_NAME,
        attempts=1,
        latency_ms=latency_ms,
        token_count=input_tokens + output_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        finish_reason=finish_reason,
        response_length=len(answer),
    )


def _generate_once(query: str, retrieved_context: str) -> GenerationResult:
    """Generate a grounded answer using the default output token budget."""
    return _generate_with_tokens(query, retrieved_context, DEFAULT_MAX_OUTPUT_TOKENS)


def generate_answer(query: str, retrieved_context: str) -> GenerationResult:
    """Generate a grounded answer with retries and short-output protection."""
    if not retrieved_context.strip():
        return GenerationResult(
            answer=REFUSAL_MESSAGE,
            model=MODEL_NAME,
            attempts=0,
            latency_ms=0.0,
            token_count=0,
            input_tokens=0,
            output_tokens=0,
            finish_reason="",
            response_length=len(REFUSAL_MESSAGE),
        )

    last_error: Exception | None = None
    retry_attempts = max(1, int(getenv("GEMINI_RETRY_ATTEMPTS") or DEFAULT_RETRY_ATTEMPTS))
    for attempt in range(1, retry_attempts + 1):
        try:
            result = _generate_once(query, retrieved_context)

            def is_max_tokens(reason: str) -> bool:
                upper = (reason or "").upper()
                return "MAX_TOKENS" in upper or "TOKEN" in upper and "MAX" in upper

            budgets = [DEFAULT_MAX_OUTPUT_TOKENS, 800, 1200]
            budget_index = 0
            while True:
                answer_text = result.answer.strip()
                needs_more = (
                    len(answer_text) < 80
                    or is_max_tokens(result.finish_reason)
                    or (len(answer_text) < 120 and not _is_complete_answer(answer_text))
                )
                if not needs_more:
                    break

                budget_index += 1
                if budget_index >= len(budgets):
                    break

                logger.warning(
                    "Gemini response looks incomplete; retrying with larger budget answer_length=%s finish_reason=%s next_budget=%s",
                    len(result.answer.strip()),
                    result.finish_reason or "UNKNOWN",
                    budgets[budget_index],
                )
                result = _generate_with_tokens(query, retrieved_context, budgets[budget_index])

            return GenerationResult(
                answer=result.answer,
                model=result.model,
                attempts=attempt,
                latency_ms=result.latency_ms,
                token_count=result.token_count,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                finish_reason=result.finish_reason,
                response_length=len(result.answer),
            )
        except Exception as exc:  # pragma: no cover - network failure path
            last_error = exc
            logger.warning("Gemini attempt %s/%s failed: %s", attempt, retry_attempts, exc)
            if attempt < retry_attempts:
                sleep(DEFAULT_RETRY_DELAY_SEC * attempt)

    logger.error("Gemini generation failed after retries: %s", last_error)
    return GenerationResult(
        answer=REFUSAL_MESSAGE,
        model=MODEL_NAME,
        attempts=retry_attempts,
        latency_ms=0.0,
        token_count=0,
        input_tokens=0,
        output_tokens=0,
        finish_reason="ERROR",
        response_length=len(REFUSAL_MESSAGE),
    )
