"""OpenAI-compatible LLM adapter."""
import json
import os
import urllib.request
import urllib.error
from typing import Any, Mapping
from vash.core.interfaces import LLMAdapter, LLMReply, RouteSettings
from vash.core.exceptions import RouteUnavailable, VashError

class Adapter(LLMAdapter):
    """OpenAI-compatible LLM adapter."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)

    def reply(self, prompt: str, route: RouteSettings) -> LLMReply:
        base_url = route.base_url or self.settings.get("base_url")
        if not base_url:
            raise VashError("base_url is required for openai_compatible", "Set models.routes.<name>.base_url")

        key_env = route.key_env or self.settings.get("key_env")
        api_key = os.environ.get(key_env, "") if key_env else ""
        if not api_key:
            raise RouteUnavailable(
                f"API key missing in env var {key_env}",
                f"Set {key_env} environment variable"
            )
        url = f"{base_url.rstrip('/')}/chat/completions"
        data = {
            "model": route.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "VASH-Engine",
            "Authorization": f"Bearer {api_key}",
            **dict(self.settings.get("headers") or {}),  # extra headers a provider documents
        }
        req = urllib.request.Request(
            url, data=json.dumps(data).encode("utf-8"),
            headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=route.timeout_s) as response:
                status, kind = response.status, response.headers.get("Content-Type", "")
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            raise RouteUnavailable(f"API error {e.code}: {e.reason}", "Check API limits or key")
        except (urllib.error.URLError, TimeoutError) as e:
            raise RouteUnavailable(f"Connection failed: {e}", "Check network connection")
        try:
            res = json.loads(body)
            text = res["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            # Say what came back: a wrong URL or a missing header often answers 200 with a non-API body.
            raise RouteUnavailable(
                f"Not a chat completion answer (HTTP {status}, {kind or 'no content type'}): {body[:160]!r}",
                "Check the API endpoint (base_url), the model name and the headers the provider needs")
        return LLMReply(text=text, route=route.name, model=route.model, degraded=False, usage=res.get("usage", {}))

    def check(self, route: RouteSettings) -> tuple[bool, str, str]:
        """The key is set and the provider lists models with it (no tokens are spent)."""
        base_url = route.base_url or self.settings.get("base_url")
        key_env = route.key_env or self.settings.get("key_env")
        api_key = os.environ.get(key_env, "") if key_env else ""
        if not base_url:
            return False, "no base_url in the route", "add base_url to the route in project-stack.json"
        if key_env and not api_key:
            return False, "the API key is missing", f"set the environment variable {key_env}"
        req = urllib.request.Request(f"{base_url.rstrip('/')}/models", method="GET", headers={
            "Accept": "application/json", "User-Agent": "VASH-Engine",
            **({"Authorization": f"Bearer {api_key}"} if api_key else {})})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
        except urllib.error.HTTPError as e:
            return False, f"{base_url} answered {e.code} {e.reason}", "check the key and the model name"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return False, f"{base_url} is not reachable ({e})", "check the network and base_url"
        return True, f"{route.model} at {base_url}: key accepted", ""
