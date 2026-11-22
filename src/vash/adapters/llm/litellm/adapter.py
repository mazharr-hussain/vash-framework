"""Client for the model gateway on the VM: an OpenAI-compatible address with one model name per kind of work.

The route's model is a kind of work (`vash-coding`, `vash-review`, ...); the gateway picks the real model. The key
is the gateway's own key (VASH_GATEWAY_KEY, or the file the VM setup writes), never a provider's key.
"""
import os
from pathlib import Path
from typing import Any, Mapping

from vash.core.interfaces import LLMReply, RouteSettings
from vash.adapters.llm.openai_compatible.adapter import Adapter as OpenAICompatible

DEFAULT_URL = "http://127.0.0.1:4000/v1"
KEY_ENV = "VASH_GATEWAY_KEY"
KEY_FILE = Path("/etc/vash/gateway-key")


def gateway_key() -> str:
    key = os.environ.get(KEY_ENV, "")
    if not key:
        path = Path(os.environ.get("VASH_GATEWAY_KEY_FILE", str(KEY_FILE)))
        try:
            key = path.read_text().strip()
        except OSError:
            key = ""
    return key


class Adapter(OpenAICompatible):
    """The gateway is OpenAI-compatible; only its address and key are filled in here."""

    def __init__(self, settings: Mapping[str, Any]):
        super().__init__({**settings, "base_url": settings.get("base_url") or DEFAULT_URL, "key_env": KEY_ENV})

    def _route(self, route: RouteSettings) -> RouteSettings:
        if gateway_key() and not os.environ.get(KEY_ENV):
            os.environ[KEY_ENV] = gateway_key()  # read once from the file the VM setup wrote
        return RouteSettings(name=route.name, adapter=route.adapter, model=route.model, vendor=route.vendor,
                             base_url=route.base_url or DEFAULT_URL, key_env=KEY_ENV, timeout_s=route.timeout_s)

    def reply(self, prompt: str, route: RouteSettings) -> LLMReply:
        return super().reply(prompt, self._route(route))

    def check(self, route: RouteSettings) -> tuple[bool, str, str]:
        if not gateway_key():
            return False, f"model gateway ({route.model}): not set up on this machine", \
                "install it on the VM: vash onboard oci --update (from Cloud Shell)"
        ok, found, fix = super().check(self._route(route))
        if not ok and "not reachable" in found:
            fix = "start the gateway: sudo systemctl start vash-gateway (vash onboard oci --update installs it)"
        return ok, found.replace(route.model, f"model gateway ({route.model})", 1), fix
