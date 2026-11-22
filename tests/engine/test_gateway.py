"""The model gateway's settings (LiteLLM): a model per kind of work, fallbacks, the VM's model last, rule R4."""
import json

from vash.adapters.llm.litellm.gateway import read_env, settings, write


def names(data):
    return [m["model_name"] for m in data["model_list"]]


def model_of(data, name):
    return next(m["litellm_params"]["model"] for m in data["model_list"] if m["model_name"] == name)


def test_no_key_every_kind_goes_to_the_vms_model():
    data = settings(set(), "qwen2.5-coder:7b")
    for kind in ("coding", "review", "docs", "prompt", "test"):
        assert model_of(data, f"vash-{kind}") == "ollama_chat/qwen2.5-coder:7b"
    assert data["general_settings"]["master_key"] == "os.environ/VASH_GATEWAY_KEY"


def test_keys_give_each_kind_its_model_and_a_fallback_chain_ending_on_the_vm():
    data = settings({"GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY"}, "qwen2.5-coder:7b")
    assert model_of(data, "vash-coding") == "cerebras/qwen-3-coder-480b"
    assert model_of(data, "vash-review") == "groq/openai/gpt-oss-120b"
    assert model_of(data, "vash-docs") == "groq/llama-3.3-70b-versatile"
    chain = next(f["vash-coding"] for f in data["litellm_settings"]["fallbacks"] if "vash-coding" in f)
    assert chain[-1] == "vash-local" and model_of(data, chain[0]) == "groq/qwen/qwen3-32b"
    keys = {m["litellm_params"].get("api_key") for m in data["model_list"]} - {None}
    assert keys <= {"os.environ/GROQ_API_KEY", "os.environ/CEREBRAS_API_KEY", "os.environ/GEMINI_API_KEY"}


def test_r4_a_kind_never_uses_the_makers_of_its_reviewer():
    # Only a Gemini key: review is Gemini (Google), so documents must not be written by Gemini too.
    data = settings({"GEMINI_API_KEY"}, "qwen2.5-coder:7b")
    assert model_of(data, "vash-review") == "gemini/gemini-2.5-flash"
    assert model_of(data, "vash-docs") == "ollama_chat/qwen2.5-coder:7b"


def test_no_model_at_all_is_explained():
    import pytest
    from vash.core.exceptions import VashError
    with pytest.raises(VashError, match="No model for the gateway"):
        settings(set(), "")


def test_written_as_json_which_is_yaml_and_keys_are_only_named(tmp_path):
    env = tmp_path / "gateway.env"
    env.write_text("GROQ_API_KEY=gsk_secret\n# comment\nEMPTY=\n")
    assert read_env(env) == {"GROQ_API_KEY": "gsk_secret"}  # pragma: allowlist secret (a test value)
    write(tmp_path / "gw.yaml", env, "qwen2.5-coder:7b")
    text = (tmp_path / "gw.yaml").read_text()
    assert "gsk_secret" not in text and json.loads(text)["model_list"]


def test_any_model_can_be_added_free_ones_at_once_paid_ones_only_when_said(tmp_path):
    import pytest
    from vash.adapters.llm.litellm.gateway import add
    from vash.core.exceptions import VashError
    extra = tmp_path / "gateway-models.json"
    add(extra, "coding", "groq/moonshotai/kimi-k2-instruct", "moonshot", "", paid=False, first=True)
    with pytest.raises(VashError, match="not in VASH's list of free providers"):
        add(extra, "docs", "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta", "TOGETHER_API_KEY",
            paid=False, first=False)
    add(extra, "docs", "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta", "TOGETHER_API_KEY",
        paid=True, first=False)
    data = settings({"GROQ_API_KEY", "TOGETHER_API_KEY"}, "qwen2.5-coder:7b", extra=extra)
    assert model_of(data, "vash-coding") == "groq/moonshotai/kimi-k2-instruct"  # added first
    docs = [m["litellm_params"]["model"] for m in data["model_list"] if m["model_name"].startswith("vash-docs")]
    assert docs[-1] == "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo"  # added last
    assert next(m["litellm_params"]["api_key"] for m in data["model_list"]
                if m["litellm_params"]["model"].startswith("together_ai/")) == "os.environ/TOGETHER_API_KEY"


def test_unknown_kind_or_model_name_is_refused(tmp_path):
    import pytest
    from vash.adapters.llm.litellm.gateway import add
    from vash.core.exceptions import VashError
    with pytest.raises(VashError, match="Unknown kind"):
        add(tmp_path / "x.json", "dance", "groq/x", "meta", "", False, False)
    with pytest.raises(VashError, match="not a LiteLLM model name"):
        add(tmp_path / "x.json", "coding", "justaname", "meta", "", False, False)
