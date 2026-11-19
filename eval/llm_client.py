"""A minimal client for OpenAI-compatible chat endpoints, standard library only.

Providers (the same chain as the Quantum Information Agent's llm.py):
    groq    free tier            GROQ_API_KEY     default model openai/gpt-oss-120b
    hf      your HF credits      HF_TOKEN         default model deepseek-ai/DeepSeek-V4-Flash-0731:deepinfra
    gemini  free tier            GOOGLE_API_KEY   default model gemini-3.8-flash
    openai  PAID                 OPENAI_API_KEY   only with ALLOW_OPENAI=1; default model gpt-4o-mini

Keys are read from the environment, then from a .env file (the environment wins). A key is never
printed, logged or written to a result file.
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "openai/gpt-oss-120b"),
    "hf": ("https://router.huggingface.co/v1", "HF_TOKEN", "deepseek-ai/DeepSeek-V4-Flash-0731:deepinfra"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GOOGLE_API_KEY", "gemini-3.8-flash"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
}


class CapReached(RuntimeError):
    pass


def load_env(path: Path) -> dict:
    """KEY=value lines of a .env file (comments and blank lines skipped, quotes and trailing comments removed)."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.split(" #")[0].strip().strip('"').strip("'")
        out[key.strip()] = value
    return out


def setting(name: str, env: dict, default: str = "") -> str:
    return os.environ.get(name) or env.get(name) or default


class Client:
    """One provider and model. chat(messages, tools) returns the assistant message dict. Every request,
    retries included, counts against max_calls."""

    def __init__(self, provider: str, model: str = "", env=None, max_calls: int = 120, timeout: int = 60):
        if provider not in PROVIDERS:
            raise ValueError(f"unknown provider {provider!r}; choose from {', '.join(PROVIDERS)}")
        env = env or {}
        base, key_name, default_model = PROVIDERS[provider]
        if provider == "openai" and setting("ALLOW_OPENAI", env) != "1":
            raise PermissionError("OpenAI is paid: set ALLOW_OPENAI=1 in .env to use it (development only)")
        self.key = setting(key_name, env)
        if not self.key:
            raise PermissionError(f"no {key_name} in the environment or in .env")
        self.provider, self.model, self.base = provider, model or default_model, base
        self.max_calls, self.timeout, self.calls = max_calls, timeout, 0

    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base}/chat/completions", data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}",
                     "User-Agent": "traceground-eval/0.1"})          # the default Python agent is blocked by some hosts
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def chat(self, messages: list, tools: list) -> dict:
        payload = {"model": self.model, "messages": messages, "tools": tools, "tool_choice": "auto",
                   "temperature": 0, "max_tokens": 1024}
        if "gpt-oss" in self.model:
            payload["reasoning_effort"] = "low"
        for attempt in range(4):
            if self.calls >= self.max_calls:
                raise CapReached(f"request cap reached ({self.max_calls} this run); raise --max-calls to go on")
            self.calls += 1
            try:
                data = self._post(payload)
                return data["choices"][0]["message"]
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:300]
                if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                    wait = min(float(e.headers.get("retry-after") or 5 * 2 ** attempt), 30.0)
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"HTTP {e.code} from {self.provider}: {body}") from None
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < 1:                       # one retry: a second timeout means the host is overloaded
                    time.sleep(5)
                    continue
                raise RuntimeError(f"cannot reach {self.provider}: {e}") from None
        raise RuntimeError("unreachable")
