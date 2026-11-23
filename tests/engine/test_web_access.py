"""The web chat: the provider's API calls (tunnel, DNS, login) and `vash onboard oci --web`."""
import json

import pytest

from vash.adapters.cloud.oci import adapter as tf_module
from vash.adapters.web.cloudflare.adapter import Adapter
from vash.core.exceptions import VashError
from vash.core.interfaces import CATEGORY_INTERFACES

from .test_oci_stack import StackCloud, no_local_terraform, stack_make

HOST = "vash.example.org"


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


class FakeApi:
    """Cloudflare's API as far as VASH uses it, kept in memory."""

    def __init__(self, records=(), refuse=None):
        self.calls = []
        self.zones = [{"id": "z1", "name": "example.org", "account": {"id": "acc1"}}]
        self.tunnels, self.policies, self.apps = [], [], []
        self.records = list(records)
        self.config = None
        self.refuse = refuse

    def __call__(self, method, path, body=None):
        self.calls.append((method, path, body))
        if self.refuse and self.refuse in path:
            return {"success": False, "status": 403, "errors": [{"code": 10000, "message": "Authentication error"}]}
        base = path.split("?")[0]
        query = path.split("?")[1] if "?" in path else ""
        if base == "/zones":
            return {"success": True, "result": [z for z in self.zones if f"name={z['name']}" == query]}
        if base == "/accounts/acc1/cfd_tunnel":
            if method == "POST":
                self.tunnels.append({"id": "t1", "name": body["name"]})
                return {"success": True, "result": self.tunnels[-1]}
            return {"success": True, "result": list(self.tunnels)}
        if base.endswith("/configurations"):
            self.config = body
            return {"success": True, "result": {}}
        if base.endswith("/token"):
            return {"success": True, "result": "eyJ-connector-token"}
        if base == "/zones/z1/dns_records":
            if method == "POST":
                self.records.append({"id": "r1", **body})
                return {"success": True, "result": self.records[-1]}
            return {"success": True, "result": [r for r in self.records if f"name={r['name']}" == query]}
        if base == "/accounts/acc1/access/policies":
            if method == "POST":
                self.policies.append({"id": "p1", **body})
                return {"success": True, "result": self.policies[-1]}
            return {"success": True, "result": list(self.policies)}
        if base == "/accounts/acc1/access/apps":
            if method == "POST":
                self.apps.append({"id": "a1", **body})
                return {"success": True, "result": self.apps[-1]}
            return {"success": True, "result": list(self.apps)}
        return {"success": True, "result": {}}


def test_the_adapter_has_the_web_interface():
    assert isinstance(Adapter({"api_token": "x"}, request=FakeApi()), CATEGORY_INTERFACES["web"])
    with pytest.raises(VashError):
        Adapter({})


def test_publish_makes_the_login_first_then_the_tunnel_and_the_address():
    api = FakeApi()
    made = Adapter({"api_token": "x"}, request=api).publish(HOST, "http://127.0.0.1:8080", ["me@example.org"])
    assert made["connector_token"] == "eyJ-connector-token" and made["url"] == f"https://{HOST}"
    assert made["created"] == ["login policy", "login (Access application)", "tunnel", "DNS record"]
    posts = [p for m, p, _ in api.calls if m == "POST"]
    assert posts.index("/accounts/acc1/access/apps") < posts.index("/accounts/acc1/cfd_tunnel")  # never open
    assert api.policies[0]["include"] == [{"email": {"email": "me@example.org"}}]
    assert api.policies[0]["decision"] == "allow"
    assert api.apps[0]["type"] == "self_hosted" and api.apps[0]["domain"] == HOST
    assert api.apps[0]["policies"] == [{"id": "p1", "precedence": 1}]
    assert api.config["config"]["ingress"] == [{"hostname": HOST, "service": "http://127.0.0.1:8080"},
                                               {"service": "http_status:404"}]
    assert api.records[0]["content"] == "t1.cfargotunnel.com" and api.records[0]["proxied"] is True


def test_a_second_run_updates_and_makes_nothing_new():
    api = FakeApi()
    adapter = Adapter({"api_token": "x"}, request=api)
    adapter.publish(HOST, "http://127.0.0.1:8080", ["me@example.org"])
    again = adapter.publish(HOST, "http://127.0.0.1:8080", ["me@example.org", "you@example.org"])
    assert again["created"] == []
    assert len(api.tunnels) == len(api.apps) == len(api.policies) == len(api.records) == 1
    puts = [p for m, p, _ in api.calls if m == "PUT"]
    assert "/accounts/acc1/access/policies/p1" in puts and "/zones/z1/dns_records/r1" in puts


def test_an_existing_other_record_is_not_overwritten():
    api = FakeApi(records=[{"id": "r0", "type": "A", "name": HOST, "content": "192.0.2.1"}])
    with pytest.raises(VashError, match="already has a A record"):
        Adapter({"api_token": "x"}, request=api).publish(HOST, "http://127.0.0.1:8080", ["me@example.org"])


def test_a_missing_permission_is_named():
    api = FakeApi(refuse="/access/policies")
    with pytest.raises(VashError) as e:
        Adapter({"api_token": "x"}, request=api).publish(HOST, "http://127.0.0.1:8080", ["me@example.org"])
    assert "Access: Apps and Policies - Edit" in e.value.fix


def test_a_domain_not_on_the_provider_is_reported():
    with pytest.raises(VashError, match="No Cloudflare domain"):
        Adapter({"api_token": "x"}, request=FakeApi()).publish("vash.other.net", "http://127.0.0.1:8080", ["a@b.org"])


def test_unpublish_removes_what_publish_made():
    api = FakeApi()
    adapter = Adapter({"api_token": "x"}, request=api)
    adapter.publish(HOST, "http://127.0.0.1:8080", ["me@example.org"])
    removed = adapter.unpublish(HOST)
    assert sorted(removed) == ["DNS record", "login (Access application)", "login policy", "tunnel"]


class WebCloud(StackCloud):
    def __init__(self, kept_token="", **kw):
        super().__init__(**kw)
        self.kept_token = kept_token  # a token kept in the vault by an earlier run

    def __call__(self, args, **kwargs):
        import base64
        from .test_onboard_oci import done
        if args[0] == "ssh" and "cat /var/lib/vash/web-ready" in args[-1]:
            self.calls.append((args, kwargs))
            return done("web=open-webui 0.13.3 active")
        if args[:3] == ["oci", "secrets", "secret-bundle"]:
            self.calls.append((args, kwargs))
            if not self.kept_token:
                return done(code=1)  # no such secret
            content = base64.b64encode(self.kept_token.encode()).decode()
            return done(json.dumps({"data": {"secret-bundle-content": {"content": content}}}))
        return super().__call__(args, **kwargs)


def test_web_publishes_and_installs_the_page_with_the_token_never_on_a_command_line(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    api = FakeApi()
    monkeypatch.setattr("vash.adapters.web.cloudflare.adapter.Adapter._http", lambda self, m, p, b=None: api(m, p, b))
    cloud = WebCloud()
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    state["stack"]["outputs"].update(vault_id="ocid1.vault..v", key_id="ocid1.key..k",
                                     compartment_ids={"security": "ocid1.compartment..sec"})
    path.write_text(json.dumps(state))
    ob = stack_make(cloud, home, web=True, web_address=HOST, web_emails=["Me@Example.org"])
    ob.secret = lambda q: "CF_TOKEN_SECRET"
    assert ob.up() == 0
    assert [x["secretName"] for x in cloud.saved_secrets] == ["vash-web-api-token"]
    tokens = [c for c in cloud.calls if c[0][0] == "ssh" and "/etc/vash/tunnel-token" in c[0][-1]]
    assert len(tokens) == 1 and tokens[0][1]["input"] == "eyJ-connector-token" and "umask 077" in tokens[0][0][-1]
    installs = [c for c in cloud.calls if c[0][0] == "ssh" and "vash-web.sh" in c[0][-1]]
    assert len(installs) == 1 and f'WEB_URL="https://{HOST}"' in installs[0][1]["input"]
    assert "@@" not in installs[0][1]["input"]
    assert all("CF_TOKEN_SECRET" not in " ".join(c[0]) and "eyJ-connector-token" not in " ".join(c[0])
               for c in cloud.calls)
    saved = json.loads(path.read_text())["web"]
    assert saved["address"] == HOST and saved["emails"] == ["me@example.org"]
    assert api.policies[0]["include"] == [{"email": {"email": "me@example.org"}}]


def test_web_a_second_time_reuses_the_kept_token_and_the_saved_answers(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    api = FakeApi()
    monkeypatch.setattr("vash.adapters.web.cloudflare.adapter.Adapter._http", lambda self, m, p, b=None: api(m, p, b))
    cloud = WebCloud(kept_token="CF_KEPT")
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    state["stack"]["outputs"].update(vault_id="ocid1.vault..v", key_id="ocid1.key..k",
                                     compartment_ids={"security": "ocid1.compartment..sec"})
    state["web"] = {"address": HOST, "emails": ["me@example.org"], "account_id": "acc1"}
    path.write_text(json.dumps(state))
    ob = stack_make(cloud, home, web=True)
    ob.secret = lambda q: pytest.fail("the token must not be asked again")
    assert ob.up() == 0
    assert api.apps[0]["domain"] == HOST


def test_web_refuses_a_bad_address_or_e_mail(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = WebCloud()
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    path.write_text(json.dumps(state))
    with pytest.raises(VashError, match="not a web address"):
        stack_make(cloud, home, web=True, web_address="http://x", web_emails=["me@example.org"]).up()
    with pytest.raises(VashError, match="Not an e-mail"):
        stack_make(cloud, home, web=True, web_address=HOST, web_emails=["me"]).up()


def test_the_web_script_serves_only_the_vms_own_interface():
    from vash.core.paths import vash_root
    script = (vash_root() / "iac" / "oci" / "cloud-init" / "vash-web.sh").read_text()
    assert "--host 127.0.0.1 --port $WEB_PORT" in script and "vash mcp --http" in script
    assert "sha256sum -c -" in script and script.count("sha256sum -c -") == 2  # page and connector checked
    assert "--token-file /etc/vash/tunnel-token" in script  # never on a command line
    assert "WEBUI_AUTH_TRUSTED_EMAIL_HEADER=Cf-Access-Authenticated-User-Email" in script  # pragma: allowlist secret (a header name)
    assert "ENABLE_SIGNUP=false" in script and "ENABLE_OLLAMA_API=false" in script


def test_the_vms_model_reads_a_long_enough_context_for_the_web_chat():
    """Seen live: with Ollama's 4k default the web chat's instructions and tool list were cut off."""
    from vash.core.paths import vash_root
    script = (vash_root() / "iac" / "oci" / "cloud-init" / "vash-runner.sh").read_text()
    assert "CONTEXT_LENGTH=16384" in script and "OLLAMA_CONTEXT_LENGTH=%s" in script
    assert script.index("ollama.service.d/vash.conf") < script.index('ollama pull "$MODEL"')
    assert 'echo "model=$MODEL"' in script  # `--keys` reads the model from this line
