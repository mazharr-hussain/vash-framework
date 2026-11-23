"""Cloudflare: a Tunnel from the VM, a DNS name for it and an Access login in front (Zero Trust Free plan).

Everything is made through Cloudflare's own API (https://developers.cloudflare.com/api/, checked against its
published OpenAPI schema on 23 Nov 2026) with one API token the owner makes once, with three permissions:
  zone <the domain> - DNS - Edit; account - Cloudflare Tunnel - Edit; account - Access: Apps and Policies - Edit.
The tunnel is "remotely managed" (its routes are kept by Cloudflare), so the VM only needs the connector token:
`cloudflared` connects out from the VM and no port is opened. Each call is idempotent: a second run finds what the
first one made and updates it.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping

from vash.core.exceptions import VashError
from vash.core.interfaces import WebAccessAdapter

API = "https://api.cloudflare.com/client/v4"
NAME = "vash"  # the tunnel, the Access application and its policy are all called this
SESSION = "24h"  # how long a login lasts
# How the owner gives the token once (vash onboard oci --web): where to make it and what it needs.
TOKEN = {"label": "Cloudflare API token",
         "signup": "https://dash.cloudflare.com/profile/api-tokens (Create Token, Custom token)",
         "permissions": ["Zone - DNS - Edit (your domain)", "Account - Cloudflare Tunnel - Edit",
                         "Account - Access: Apps and Policies - Edit"]}
# Which permission a refused call needs, for the fix shown to the owner.
NEEDS = {"zones": "Zone - DNS - Edit", "dns_records": "Zone - DNS - Edit", "cfd_tunnel": "Account - Cloudflare Tunnel - Edit",
         "access": "Account - Access: Apps and Policies - Edit"}

Request = Callable[[str, str, Any], dict[str, Any]]


class Adapter(WebAccessAdapter):
    """settings: {api_token, account_id (optional: read from the domain's zone when missing), name (optional)}."""

    def __init__(self, settings: Mapping[str, Any], request: Request | None = None):
        super().__init__(settings)
        self.token = str(settings.get("api_token") or "")
        if not self.token:
            raise VashError("No Cloudflare API token", "Give it with `vash onboard oci --web`")
        self.name = str(settings.get("name") or NAME)
        self._account = str(settings.get("account_id") or "")
        self._request = request or self._http

    # ---- the API -------------------------------------------------------
    def _http(self, method: str, path: str, body: Any = None) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(API + path, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                answer = json.loads(e.read().decode() or "{}")
            except ValueError:
                answer = {}
            answer.setdefault("success", False)
            answer["status"] = e.code
            return answer
        except urllib.error.URLError as e:
            raise VashError(f"Cloudflare could not be reached ({e.reason})", "Check the network and try again")

    def call(self, method: str, path: str, body: Any = None) -> Any:
        answer = self._request(method, path, body)
        if answer.get("success", True):
            return answer.get("result")
        errors = "; ".join(f"{x.get('code')}: {x.get('message')}" for x in answer.get("errors") or []) or "refused"
        part = next((v for k, v in NEEDS.items() if f"/{k}" in path), "")
        if answer.get("status") in (401, 403) or "auth" in errors.lower():
            raise VashError(f"Cloudflare refused {method} {path.split('?')[0]}: {errors}",
                            f"The API token needs the permission '{part}'; edit it at {TOKEN['signup'].split(' ')[0]}")
        raise VashError(f"Cloudflare refused {method} {path.split('?')[0]}: {errors}",
                        "Check the domain and the Zero Trust team in the Cloudflare dashboard, then run it again")

    # ---- the pieces ----------------------------------------------------
    def zone(self, hostname: str) -> dict[str, Any]:
        """The domain (zone) that holds hostname: vash.example.org, then example.org, ..."""
        parts = hostname.lower().strip(".").split(".")
        for i in range(len(parts) - 1):
            found = self.call("GET", f"/zones?name={'.'.join(parts[i:])}") or []
            if found:
                return found[0]
        raise VashError(f"No Cloudflare domain holds {hostname}",
                        "Add the domain to Cloudflare (its name servers must point there) and give the token "
                        "'Zone - DNS - Edit' on it")

    def account(self, zone: Mapping[str, Any]) -> str:
        if not self._account:
            self._account = str((zone.get("account") or {}).get("id") or "")
        if not self._account:
            raise VashError("The Cloudflare account id is not known",
                            "Copy it from the dashboard (the domain's Overview page, Account ID) when asked")
        return self._account

    def tunnel(self, account: str) -> tuple[dict[str, Any], bool]:
        found = self.call("GET", f"/accounts/{account}/cfd_tunnel?name={self.name}&is_deleted=false") or []
        if found:
            return found[0], False
        return self.call("POST", f"/accounts/{account}/cfd_tunnel", {"name": self.name, "config_src": "cloudflare"}), True

    def route(self, account: str, tunnel_id: str, hostname: str, service: str) -> None:
        """The tunnel sends hostname to the local service; anything else gets 404."""
        self.call("PUT", f"/accounts/{account}/cfd_tunnel/{tunnel_id}/configurations",
                  {"config": {"ingress": [{"hostname": hostname, "service": service}, {"service": "http_status:404"}]}})

    def dns(self, zone_id: str, hostname: str, tunnel_id: str) -> bool:
        """A proxied CNAME hostname -> <tunnel>.cfargotunnel.com; returns True when it was made now."""
        record = {"type": "CNAME", "name": hostname, "content": f"{tunnel_id}.cfargotunnel.com", "proxied": True,
                  "comment": "VASH web page (Cloudflare Tunnel)"}
        found = self.call("GET", f"/zones/{zone_id}/dns_records?name={hostname}") or []
        other = [r for r in found if r.get("type") != "CNAME"]
        if other:
            raise VashError(f"{hostname} already has a {other[0].get('type')} record ({other[0].get('content')})",
                            "Delete that record in the Cloudflare dashboard (DNS, Records), or choose another "
                            "address, then run it again")
        if found:
            self.call("PUT", f"/zones/{zone_id}/dns_records/{found[0]['id']}", record)
            return False
        self.call("POST", f"/zones/{zone_id}/dns_records", record)
        return True

    def policy(self, account: str, emails: list[str]) -> tuple[str, bool]:
        """A reusable Access policy that allows the owner's e-mail addresses (a one-time PIN is sent to them)."""
        body = {"name": f"{self.name}-owner", "decision": "allow", "session_duration": SESSION,
                "include": [{"email": {"email": e}} for e in emails]}
        found = [p for p in self.call("GET", f"/accounts/{account}/access/policies") or []
                 if p.get("name") == body["name"]]
        if found:
            self.call("PUT", f"/accounts/{account}/access/policies/{found[0]['id']}", body)
            return found[0]["id"], False
        return self.call("POST", f"/accounts/{account}/access/policies", body)["id"], True

    def application(self, account: str, hostname: str, policy_id: str) -> bool:
        body = {"name": self.name.upper(), "type": "self_hosted", "domain": hostname, "session_duration": SESSION,
                "app_launcher_visible": False, "policies": [{"id": policy_id, "precedence": 1}]}
        found = [a for a in self.call("GET", f"/accounts/{account}/access/apps") or []
                 if str(a.get("domain", "")).lower() == hostname]
        if found:
            self.call("PUT", f"/accounts/{account}/access/apps/{found[0]['id']}", body)
            return False
        self.call("POST", f"/accounts/{account}/access/apps", body)
        return True

    # ---- the interface -------------------------------------------------
    def publish(self, hostname: str, service: str, emails: list[str]) -> dict[str, Any]:
        hostname = hostname.lower().strip(".")
        if not emails:
            raise VashError("No e-mail address is allowed to log in", "Give at least one e-mail address")
        zone = self.zone(hostname)
        account = self.account(zone)
        created: list[str] = []
        # The login comes first: the address is never open without it, not even for a moment.
        policy_id, made = self.policy(account, emails)
        created += ["login policy"] if made else []
        if self.application(account, hostname, policy_id):
            created.append("login (Access application)")
        tunnel, made = self.tunnel(account)
        created += ["tunnel"] if made else []
        self.route(account, tunnel["id"], hostname, service)
        if self.dns(zone["id"], hostname, tunnel["id"]):
            created.append("DNS record")
        token = self.call("GET", f"/accounts/{account}/cfd_tunnel/{tunnel['id']}/token")
        return {"connector_token": token, "url": f"https://{hostname}", "created": created, "tunnel_id": tunnel["id"]}

    def unpublish(self, hostname: str) -> list[str]:
        hostname = hostname.lower().strip(".")
        zone = self.zone(hostname)
        account = self.account(zone)
        removed: list[str] = []
        for r in self.call("GET", f"/zones/{zone['id']}/dns_records?name={hostname}") or []:
            if r.get("type") == "CNAME" and str(r.get("content", "")).endswith(".cfargotunnel.com"):
                self.call("DELETE", f"/zones/{zone['id']}/dns_records/{r['id']}")
                removed.append("DNS record")
        for a in self.call("GET", f"/accounts/{account}/access/apps") or []:
            if str(a.get("domain", "")).lower() == hostname:
                self.call("DELETE", f"/accounts/{account}/access/apps/{a['id']}")
                removed.append("login (Access application)")
        for p in self.call("GET", f"/accounts/{account}/access/policies") or []:
            if p.get("name") == f"{self.name}-owner":
                self.call("DELETE", f"/accounts/{account}/access/policies/{p['id']}")
                removed.append("login policy")
        for t in self.call("GET", f"/accounts/{account}/cfd_tunnel?name={self.name}&is_deleted=false") or []:
            self.call("DELETE", f"/accounts/{account}/cfd_tunnel/{t['id']}/connections")
            self.call("DELETE", f"/accounts/{account}/cfd_tunnel/{t['id']}")
            removed.append("tunnel")
        return removed
