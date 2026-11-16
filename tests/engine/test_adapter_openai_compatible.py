"""Tests for OpenAI-compatible LLM adapter."""
import json
import pytest
from unittest.mock import patch, MagicMock
from vash.adapters.llm.openai_compatible.adapter import Adapter
from vash.core.interfaces import RouteSettings
from vash.core.exceptions import RouteUnavailable, VashError

@patch("urllib.request.urlopen")
def test_reply(mock_urlopen, monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret")
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"choices": [{"message": {"content": "Hi"}}], "usage": {"total_tokens": 10}}).encode()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    res = adapter.reply("Prompt", route)
    assert res.text == "Hi"

def test_missing_key():
    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    with patch.dict("os.environ", clear=True):
        with pytest.raises(RouteUnavailable, match="API key missing"):
            adapter.reply("Prompt", route)

def test_missing_settings():
    adapter = Adapter({})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url=None, key_env=None, timeout_s=10)
    with pytest.raises(VashError, match="base_url is required"):
        adapter.reply("Prompt", route)

@patch("urllib.request.urlopen")
def test_http_error(mock_urlopen, monkeypatch):
    import urllib.error
    monkeypatch.setenv("TEST_KEY", "secret")
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 401, "Unauthorized", {}, None)
    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    with pytest.raises(RouteUnavailable, match="API error 401"):
        adapter.reply("Prompt", route)

@patch("urllib.request.urlopen")
def test_timeout(mock_urlopen, monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret")
    mock_urlopen.side_effect = TimeoutError("timed out")
    adapter = Adapter({"base_url": "http://test", "key_env": "TEST_KEY"})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    with pytest.raises(RouteUnavailable, match="Connection failed"):
        adapter.reply("Prompt", route)

@patch("urllib.request.urlopen")
def test_a_non_api_answer_says_what_came_back_and_extra_headers_are_sent(mock_urlopen, monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret")
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"OK"
    mock_resp.status = 200
    mock_resp.headers.get.return_value = "text/plain"
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    adapter = Adapter({"headers": {"X-Api-Version": "1"}})
    route = RouteSettings(name="test", adapter="openai_compatible", model="gpt", vendor="test", base_url="http://test", key_env="TEST_KEY", timeout_s=10)
    with pytest.raises(RouteUnavailable, match=r"HTTP 200, text/plain\): 'OK'"):
        adapter.reply("Prompt", route)
    sent = mock_urlopen.call_args[0][0]
    assert sent.get_header("X-api-version") == "1" and sent.get_header("Accept") == "application/json"
