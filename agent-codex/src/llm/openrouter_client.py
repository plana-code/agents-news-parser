import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


DEFAULT_OPENROUTER_API_KEY = (
    "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"
)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
FREE_MODEL_FALLBACKS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemma-7b-it:free",
    "mistralai/mistral-7b-instruct:free",
]


@dataclass
class NewsItem:
    title: str
    description: str
    publication_date: Optional[str] = None


def _api_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", DEFAULT_OPENROUTER_API_KEY)


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/openai/codex",  # optional per OpenRouter
        "X-Title": "Smart News Aggregator",
    }


def discover_free_models(session: Optional[requests.Session] = None) -> List[str]:
    s = session or requests.Session()
    try:
        logging.getLogger(__name__).debug("Discovering OpenRouter models…")
        resp = s.get(f"{OPENROUTER_BASE}/models", headers=_headers(), timeout=20)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("data", [])
        free = []
        for m in models:
            name = m.get("id") or m.get("name")
            pricing = m.get("pricing") or {}
            is_free = False
            # Heuristic: free models often have prompt and completion price 0 or missing
            if pricing:
                prompt = pricing.get("prompt")
                completion = pricing.get("completion")
                if (prompt in (0, None) and completion in (0, None)) or m.get(
                    "free"
                ) is True:
                    is_free = True
            else:
                is_free = True

            # Exclude reasoning-tagged models
            tags = (m.get("tags") or []) + (
                m.get("meta", {}).get("tags", [])
                if isinstance(m.get("meta"), dict)
                else []
            )
            if any("reason" in str(t).lower() for t in tags):
                continue

            if name and is_free:
                free.append(name)
        # Keep stable order but prioritize known good ones
        prioritized = [m for m in FREE_MODEL_FALLBACKS if m in free]
        others = [m for m in free if m not in prioritized]
        combined = prioritized + others
        logging.getLogger(__name__).info("Free models: %s", combined[:5])
        return combined or FREE_MODEL_FALLBACKS.copy()
    except Exception as e:
        logging.getLogger(__name__).warning("Model discovery failed: %s", e)
        return FREE_MODEL_FALLBACKS.copy()


def desired_models(session: Optional[requests.Session] = None) -> List[str]:
    override = os.getenv("OPENROUTER_MODEL")
    if override:
        models = [m.strip() for m in override.split(",") if m.strip()]
        logging.getLogger(__name__).info("Using OPENROUTER_MODEL override: %s", models)
        return models
    free = discover_free_models(session)
    return free or FREE_MODEL_FALLBACKS.copy()


def _build_prompt(truncated_html: str) -> List[Dict[str, str]]:
    system = (
        "You are a precise information extraction engine. Extract top news from the given HTML. "
        "Return ONLY compact JSON array. Each item: title (string), description (string), publication_date (string or null). "
        "Do not include any extra keys or text. Use Russian if content is Russian."
    )
    user = (
        "From the HTML or text below, extract up to 20 most important news items. "
        "Prefer homepage major headlines. If publication dates present, include them.\n\nCONTENT:\n"
        + truncated_html
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _build_prompt_fallback(content: str) -> List[Dict[str, str]]:
    system = (
        "You extract news as strict JSON. If uncertain, infer concise descriptions. "
        "Return ONLY a JSON array of at least 5 items with keys: title, description, publication_date."
    )
    user = (
        "From the list below, output at least 5 news items as JSON objects. "
        "Only include title and a short description; set publication_date to null if unknown.\n\nLIST:\n"
        + content
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _truncate_html(html: str, max_chars: int = 8000) -> str:
    if len(html) <= max_chars:
        return html
    # Keep first and last chunks
    head = html[: max_chars // 2]
    tail = html[-max_chars // 2 :]
    out = head + "\n<!-- truncated -->\n" + tail
    logging.getLogger(__name__).debug("Truncated content to %s chars", len(out))
    return out


def _extract_json_block(text: str) -> str:
    # Clean common artifacts
    cleaned = text.replace("[/s]", "").strip()
    # Prefer fenced code blocks
    fence = re.search(
        r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE
    )
    if fence:
        inner = fence.group(1).strip()
        return inner
    # Fallback: first [...] or {...}
    candidates = re.findall(r"(\[[\s\S]*?\]|\{[\s\S]*?\})", cleaned)
    for c in candidates:
        c_strip = c.strip()
        token = c_strip.upper()
        if token in ("[OUT]", "[OK]", "[DONE]", "[BOS]", "[EOS]", "[INST]", "[/INST]"):
            continue
        # Skip bracket tokens that have no JSON-looking characters
        if c_strip.startswith("[") and not (
            ":" in c_strip or '"' in c_strip or "{" in c_strip
        ):
            continue
        if (
            '"title"' in c_strip
            or '"description"' in c_strip
            or c_strip.startswith("[")
        ):
            return c_strip
    if candidates:
        return candidates[0].strip()
    return cleaned


@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
def extract_news_from_html(
    html: str, session: Optional[requests.Session] = None
) -> List[NewsItem]:
    s = session or requests.Session()
    models = desired_models(s)
    truncated = _truncate_html(html)
    messages = _build_prompt(truncated)

    last_err: Optional[Exception] = None
    for model in models:
        try:
            logging.getLogger(__name__).info("LLM call model=%s", model)
            payload = {
                "model": model,
                "messages": messages,
                # Disable reasoning if available via provider flags (heuristic: keep minimal)
                "provider": {"allow_fallbacks": True},
                "temperature": 0.3,
                "max_tokens": 1200,
            }
            resp = s.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=_headers(),
                json=payload,
                timeout=60,
            )
            logging.getLogger(__name__).debug(
                "LLM response status=%s", resp.status_code
            )
            if resp.status_code == 404:
                logging.getLogger(__name__).info(
                    "Model not available (404), skipping: %s", model
                )
                continue
            if resp.status_code in (401, 403):
                # Auth issues: bubble up quickly
                resp.raise_for_status()
            if resp.status_code >= 500:
                # Let retry policy handle transient 5xx
                resp.raise_for_status()
            # For 200..399 but not 2xx, still try to parse; else ensure it's OK
            resp.raise_for_status()
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            content = _extract_json_block(content)
            if not content.strip():
                logging.getLogger(__name__).warning(
                    "Empty content from model=%s; trying next model", model
                )
                continue
            parsed = json.loads(content)
            # Accept both object with key and raw array
            items = parsed.get("items") if isinstance(parsed, dict) else parsed
            result: List[NewsItem] = []
            if isinstance(items, list):
                for it in items:
                    title = str(it.get("title", "")).strip()
                    desc = str(it.get("description", "")).strip()
                    pub = it.get("publication_date")
                    if not title or not desc:
                        continue
                    result.append(
                        NewsItem(
                            title=title,
                            description=desc,
                            publication_date=str(pub) if pub else None,
                        )
                    )
            logging.getLogger(__name__).info("Parsed items=%s", len(result))
            if result:
                return result
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).warning("LLM attempt failed (%s): %s", model, e)
            last_err = e
            continue
    # Fallback prompt if no items extracted
    try:
        fb_messages = _build_prompt_fallback(truncated)
        for model in models or FREE_MODEL_FALLBACKS:
            try:
                payload = {
                    "model": model,
                    "messages": fb_messages,
                    "provider": {"allow_fallbacks": True},
                    "temperature": 0.3,
                    "max_tokens": 1200,
                }
                resp = s.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers=_headers(),
                    json=payload,
                    timeout=60,
                )
                if resp.status_code == 404:
                    logging.getLogger(__name__).info(
                        "Fallback: model not available (404), skipping: %s", model
                    )
                    continue
                if resp.status_code in (401, 403) or resp.status_code >= 500:
                    resp.raise_for_status()
                resp.raise_for_status()
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                content = _extract_json_block(content)
                if not content.strip():
                    continue
                parsed = json.loads(content)
                items = parsed.get("items") if isinstance(parsed, dict) else parsed
                result: List[NewsItem] = []
                if isinstance(items, list):
                    for it in items:
                        title = str(it.get("title", "")).strip()
                        desc = str(it.get("description", "")).strip()
                        pub = it.get("publication_date")
                        if not title or not desc:
                            continue
                        result.append(
                            NewsItem(
                                title=title,
                                description=desc,
                                publication_date=str(pub) if pub else None,
                            )
                        )
                if result:
                    logging.getLogger(__name__).info(
                        "Fallback parsed items=%s", len(result)
                    )
                    return result
            except Exception:
                continue
    except Exception:
        pass
    # If all models failed, return empty set rather than raising to UI
    if last_err:
        logging.getLogger(__name__).warning(
            "All models failed; returning empty list: %s", last_err
        )
    return []
