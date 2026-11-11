"""Small helpers for the Gemini Decisions API codelab.

Needs google-genai 3.2 or later and a GEMINI_API_KEY environment variable.
"""
import base64
import pathlib
import time

from google import genai

MODEL = "gemini-decision-1"
USD_PER_1M_INPUT_TOKENS = 0.10  # paid tier; output tokens are always 0

MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
    ".wav": "audio/wav", ".mp3": "audio/mp3", ".m4a": "audio/m4a",
    ".mp4": "video/mp4", ".mov": "video/mov", ".pdf": "application/pdf",
}
KIND = {"image": "image", "audio": "audio", "video": "video", "application": "document"}

_client = None


def client():
    global _client
    if _client is None:
        _client = genai.Client(http_options={"api_version": "v1beta"})
    return _client


# ---- input blocks ----
def text(s):
    return {"type": "text", "text": s}


def media(path, resolution=None, data=None):
    """Turn a local image, audio, video or PDF file into an inline input block."""
    path = pathlib.Path(path)
    mime = MIME[path.suffix.lower()]
    kind = KIND[mime.split("/")[0]]
    raw = data if data is not None else path.read_bytes()
    block = {"type": kind, "data": base64.b64encode(raw).decode(), "mime_type": mime}
    if resolution and kind in ("image", "video"):
        block["resolution"] = resolution  # low, medium, high or ultra_high (images only)
    return block


# ---- question builders ----
def yes_no(question, yes=None, no=None):
    q = {"type": "noul", "instructions": question}
    if yes or no:
        q["criteria"] = {"true_description": yes or "", "false_description": no or ""}
    return q


def choice(question, options):
    """options: a dict of {option: description} or a list of option names."""
    if not isinstance(options, dict):
        options = {o: "" for o in options}
    return {"type": "choice", "instructions": question, "criteria": options}


def score(question, levels):
    """levels: descriptions ordered from lowest to highest."""
    return {"type": "score", "instructions": question, "criteria": list(levels)}


# ---- the call ----
def decide(input, questions, retries=5):
    """Run one Decisions API call. Returns (answers, info)."""
    for attempt in range(retries + 1):
        start = time.perf_counter()
        try:
            result = client().decisions.create(model=MODEL, input=input, questions=questions)
            break
        except Exception as e:
            # 429 means rate limited (the free tier allows 50,000 tokens a minute): wait and try again
            if getattr(e, "status_code", None) != 429 or attempt == retries:
                raise
            time.sleep(15 * (attempt + 1))
    tokens = result.usage.total_input_tokens
    info = {
        "ms": round((time.perf_counter() - start) * 1000),
        "input_tokens": tokens,
        "output_tokens": result.usage.total_output_tokens,
        "usd": tokens * USD_PER_1M_INPUT_TOKENS / 1_000_000,
    }
    return result.answers, info
