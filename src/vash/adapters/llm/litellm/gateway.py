"""The model gateway's settings, written by VASH (never by hand): a model per kind of work, with fallbacks.

For each kind of work (catalog/llm/gateway.json) the models whose provider key is present are chained: `vash-<kind>`
is the first, `vash-<kind>-2` the next, ... and `vash-local` (the VM's own model) the last. A kind with no key at
all goes straight to the VM's model. Rule R4 is applied here: a kind of work skips models from the maker of its
first review model. LiteLLM reads YAML, and JSON is YAML, so no YAML library is needed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vash.core.exceptions import VashError
from vash.core.paths import vash_root

LOCAL = "vash-local"
PORT = 4000


def catalog() -> dict[str, Any]:
    return json.loads((vash_root() / "catalog" / "llm" / "gateway.json").read_text())


def read_env(path: Path) -> dict[str, str]:
    """KEY=value lines of the gateway's key file (only the names are used here; values stay in that file)."""
    out: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() and not key.strip().startswith("#") and value.strip():
                out[key.strip()] = value.strip()
    return out


def chains(cat: dict[str, Any], keys: set[str]) -> dict[str, list[dict[str, str]]]:
    providers = cat["providers"]
    return {kind: [m for m in models if providers[m["provider"]]["key_env"] in keys]
            for kind, models in cat["kinds"].items()}


def apply_makers(cat: dict[str, Any], available: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
    """Rule R4: a kind of work never uses a model from the same maker as the first model that reviews it. Such a
    model is skipped for that kind (the next model, or the VM's model, writes instead); setup never fails on it."""
    out = dict(available)
    for kind, reviewer in cat.get("reviewed_by", {}).items():
        review = available.get(reviewer, [])
        if review:
            out[kind] = [m for m in available.get(kind, []) if m["maker"] != review[0]["maker"]]
    return out


def settings(keys: set[str], local_model: str, ollama_url: str = "http://127.0.0.1:11434") -> dict[str, Any]:
    cat = catalog()
    available = apply_makers(cat, chains(cat, keys))
    model_list: list[dict[str, Any]] = []
    fallbacks: list[dict[str, list[str]]] = []
    if local_model:
        model_list.append({"model_name": LOCAL, "litellm_params": {"model": f"ollama_chat/{local_model}",
                                                                   "api_base": ollama_url}})
    for kind, models in available.items():
        names = [f"vash-{kind}" if i == 0 else f"vash-{kind}-{i + 1}" for i in range(len(models))]
        for name, m in zip(names, models):
            key_env = cat["providers"][m["provider"]]["key_env"]
            model_list.append({"model_name": name, "model_info": {"maker": m["maker"]},
                               "litellm_params": {"model": m["model"], "api_key": f"os.environ/{key_env}"}})
        chain = names[1:] + ([LOCAL] if local_model else [])
        if not names:  # no key for this kind: the VM's model does it
            if local_model:
                model_list.append({"model_name": f"vash-{kind}", "litellm_params": {
                    "model": f"ollama_chat/{local_model}", "api_base": ollama_url}})
            continue
        if chain:
            fallbacks.append({names[0]: chain})
            fallbacks += [{names[i]: chain[i:]} for i in range(1, len(names))]
    if not model_list:
        raise VashError("No model for the gateway: no provider key and no model on this VM",
                        "Add a provider key (vash onboard oci --keys) or pull a model on the VM")
    return {
        "model_list": model_list,
        # A model that fails or is rate limited rests a minute; the call moves along the chain to the next one.
        "router_settings": {"num_retries": 1, "allowed_fails": 1, "cooldown_time": 60},
        "litellm_settings": {"fallbacks": fallbacks, "drop_params": True, "request_timeout": 600},
        "general_settings": {"master_key": "os.environ/VASH_GATEWAY_KEY"},
    }


def write(out: Path, env_file: Path, local_model: str) -> dict[str, Any]:
    data = settings(set(read_env(env_file)), local_model)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n")
    return data
