"""Existing compartments, VCNs and subnets: list them, delete chosen ones, pick a subnet.

Used by `vash onboard oci` before it builds anything. Every delete is asked twice
(the choice, then the exact list after a dependency check), a VM also needs its name
typed, and OCI itself refuses to delete a subnet or VCN that is still in use.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Row:
    no: int
    kind: str  # Compartment | VCN | Subnet | VM
    name: str
    state: str
    parent: str  # compartment of a VCN, VCN of a subnet
    public: str  # subnets: yes/no; VMs: public IP
    ocid: str
    compartment_id: str
    vcn_id: str = ""


class Inventory:
    def __init__(self, oci: Callable[..., Any], echo: Callable[[str], None]):
        self.oci = oci
        self.echo = echo

    # ---- reading -------------------------------------------------------
    def rows(self, tenancy: str) -> list[Row]:
        comps = self.oci("iam", "compartment", "list", "--compartment-id", tenancy,
                         "--compartment-id-in-subtree", "true", "--lifecycle-state", "ACTIVE",
                         "--access-level", "ACCESSIBLE", "--all").get("data", [])
        names = {tenancy: "(root)"}
        names.update({c["id"]: c["name"] for c in comps})
        vcns = self.oci("search", "resource", "structured-search",
                        "--query-text", "query vcn resources").get("data", {}).get("items", [])
        rows: list[Row] = []
        for c in comps:
            rows.append(Row(len(rows) + 1, "Compartment", c["name"], c.get("lifecycle-state", ""),
                            names.get(c.get("compartment-id", ""), ""), "", c["id"], c.get("compartment-id", "")))
        for v in vcns:
            if v.get("lifecycle-state") == "TERMINATED":
                continue
            comp = v.get("compartment-id", "")
            rows.append(Row(len(rows) + 1, "VCN", v.get("display-name", ""), v.get("lifecycle-state", ""),
                            names.get(comp, comp), "", v["identifier"], comp))
            subnets = self.oci("network", "subnet", "list", "--compartment-id", comp,
                               "--vcn-id", v["identifier"], "--all").get("data", [])
            for s in subnets:
                rows.append(Row(len(rows) + 1, "Subnet", s.get("display-name", ""), s.get("lifecycle-state", ""),
                                v.get("display-name", ""), "no" if s.get("prohibit-public-ip-on-vnic", True) else "yes",
                                s["id"], s.get("compartment-id", comp), v["identifier"]))
        vms = self.oci("search", "resource", "structured-search",
                       "--query-text", "query instance resources").get("data", {}).get("items", [])
        for vm in vms:
            state = vm.get("lifecycle-state", "")
            if state in ("TERMINATED", "TERMINATING"):
                continue
            ip = ""
            if state == "RUNNING":
                vnics = self.oci("compute", "instance", "list-vnics", "--instance-id", vm["identifier"]).get("data", [])
                ip = next((v.get("public-ip") for v in vnics if v.get("public-ip")), "") or ""
            comp = vm.get("compartment-id", "")
            rows.append(Row(len(rows) + 1, "VM", vm.get("display-name", ""), state,
                            names.get(comp, comp), ip, vm["identifier"], comp))
        return rows

    def show(self, rows: list[Row]) -> None:
        headers = ("S.No", "Type", "Name", "State", "Belongs to", "Public", "OCID")
        table = [headers] + [(str(r.no), r.kind, r.name, r.state, r.parent, r.public, r.ocid) for r in rows]
        widths = [max(len(row[i]) for row in table) for i in range(len(headers))]
        line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        self.echo(line)
        for i, row in enumerate(table):
            self.echo("| " + " | ".join(cell.ljust(widths[j]) for j, cell in enumerate(row)) + " |")
            if i == 0:
                self.echo(line)
        self.echo(line)

    @staticmethod
    def select(rows: list[Row], answer: str) -> tuple[list[Row], list[str]]:
        """Rows chosen by S.No or OCID (comma separated), and the entries that matched nothing."""
        by_no = {str(r.no): r for r in rows}
        by_id = {r.ocid: r for r in rows}
        chosen, unknown = [], []
        for part in (p.strip() for p in answer.split(",")):
            if not part:
                continue
            row = by_no.get(part) or by_id.get(part)
            if row is None:
                unknown.append(part)
            elif row not in chosen:
                chosen.append(row)
        return chosen, unknown

    # ---- dependencies --------------------------------------------------
    def vm_vnics(self, vm_ocid: str) -> set[str]:
        data = self.oci("compute", "instance", "list-vnics", "--instance-id", vm_ocid).get("data", [])
        return {v["id"] for v in data if v.get("id")}

    def _users_of_subnet(self, subnet_id: str, ignore: frozenset[str] = frozenset()) -> list[str]:
        """Everything holding an IP in the subnet (VMs, databases, load balancers...),
        except the VNICs of VMs deleted in the same batch."""
        ips = self.oci("network", "private-ip", "list", "--subnet-id", subnet_id, "--all").get("data", [])
        return [f"IP {ip.get('ip-address', '')} ({ip.get('display-name') or ip.get('hostname-label') or ip.get('vnic-id', '')})"
                for ip in ips if ip.get("vnic-id") not in ignore]

    def dependencies(self, r: Row, ignore: frozenset[str] = frozenset()) -> tuple[list[str], list[str]]:
        """(also deleted with it, still using it). Anything in the second list blocks the delete.

        `ignore` holds the VNIC ids of VMs chosen in the same batch: they go first, so their IPs
        do not block their subnet or VCN.
        """
        also: list[str] = []
        blockers: list[str] = []
        if r.kind == "VM":
            vm = self.oci("compute", "instance", "get", "--instance-id", r.ocid).get("data", {})
            comp = vm.get("compartment-id", r.compartment_id)
            boots = self.oci("compute", "boot-volume-attachment", "list", "--availability-domain",
                             vm.get("availability-domain", ""), "--compartment-id", comp,
                             "--instance-id", r.ocid).get("data", [])
            also += [f"boot volume {b.get('boot-volume-id', '')} (its disk: all data on it is lost)" for b in boots]
            vols = self.oci("compute", "volume-attachment", "list", "--compartment-id", comp,
                            "--instance-id", r.ocid, "--all").get("data", [])
            also += [f"block volume {v.get('volume-id', '')}: detached and kept" for v in vols
                     if v.get("lifecycle-state") == "ATTACHED"]
        elif r.kind == "Subnet":
            blockers += self._users_of_subnet(r.ocid, ignore)
        elif r.kind == "VCN":
            vcn = self.oci("network", "vcn", "get", "--vcn-id", r.ocid).get("data", {})
            comp = vcn.get("compartment-id", r.compartment_id)
            defaults = {vcn.get("default-route-table-id"), vcn.get("default-security-list-id"),
                        vcn.get("default-dhcp-options-id")}
            for s in self._children("subnet", comp, r.ocid):
                name = s.get("display-name", s["id"])
                also.append(f"subnet {name}")
                blockers += [f"subnet {name}: {u}" for u in self._users_of_subnet(s["id"], ignore)]
            for kind in ("internet-gateway", "nat-gateway", "service-gateway", "nsg",
                         "route-table", "security-list", "dhcp-options"):
                for item in self._children(kind, comp, r.ocid):
                    if item["id"] not in defaults:
                        also.append(f"{kind} {item.get('display-name', item['id'])}")
            for kind in ("local-peering-gateway", "drg-attachment"):
                for item in self._children(kind, comp, r.ocid):
                    blockers.append(f"{kind} {item.get('display-name', item['id'])} (remove it first)")
        elif r.kind == "Compartment":
            found = self.oci("search", "resource", "structured-search", "--query-text",
                             f"query all resources where compartmentId = '{r.ocid}'").get("data", {}).get("items", [])
            for item in found:
                if item.get("lifecycle-state") not in ("TERMINATED", "DELETED"):
                    blockers.append(f"{item.get('resource-type', '')} {item.get('display-name', item.get('identifier', ''))}")
        return also, blockers

    # ---- deleting ------------------------------------------------------
    def delete(self, chosen: list[Row]) -> None:
        """VMs first, then subnets, then VCNs (with their gateways, tables and lists), then compartments."""
        for r in chosen:
            if r.kind == "VM":
                self.oci("compute", "instance", "terminate", "--instance-id", r.ocid,
                         "--preserve-boot-volume", "false", "--force", "--wait-for-state", "TERMINATED")
                self.echo(f"VM {r.name} terminated")
        vcn_ids = {r.ocid for r in chosen if r.kind == "VCN"}
        for r in chosen:
            if r.kind == "Subnet" and r.vcn_id not in vcn_ids:
                self._delete_subnet(r.ocid, r.name)
        for r in chosen:
            if r.kind == "VCN":
                self._delete_vcn(r)
        for r in chosen:
            if r.kind == "Compartment":
                self.oci("iam", "compartment", "delete", "--compartment-id", r.ocid, "--force")
                self.echo(f"Compartment {r.name}: deletion started (OCI finishes it in the background)")

    def _delete_subnet(self, ocid: str, name: str) -> None:
        self.oci("network", "subnet", "delete", "--subnet-id", ocid, "--force", "--wait-for-state", "TERMINATED")
        self.echo(f"Subnet {name} deleted")

    def _children(self, kind: str, comp: str, vcn: str) -> list[dict]:
        return self.oci("network", kind, "list", "--compartment-id", comp, "--vcn-id", vcn, "--all").get("data", [])

    def _delete_vcn(self, r: Row) -> None:
        vcn = self.oci("network", "vcn", "get", "--vcn-id", r.ocid).get("data", {})
        comp = vcn.get("compartment-id", r.compartment_id)
        defaults = {vcn.get("default-route-table-id"), vcn.get("default-security-list-id"),
                    vcn.get("default-dhcp-options-id")}
        for s in self._children("subnet", comp, r.ocid):
            self._delete_subnet(s["id"], s.get("display-name", s["id"]))
        for rt in self._children("route-table", comp, r.ocid):
            if rt["id"] in defaults:
                self.oci("network", "route-table", "update", "--rt-id", rt["id"], "--route-rules", "[]", "--force")
            else:
                self.oci("network", "route-table", "delete", "--rt-id", rt["id"], "--force",
                         "--wait-for-state", "TERMINATED")
        for kind, flag in (("internet-gateway", "--ig-id"), ("nat-gateway", "--nat-gateway-id"),
                           ("service-gateway", "--service-gateway-id"), ("nsg", "--nsg-id")):
            for item in self._children(kind, comp, r.ocid):
                self.oci("network", kind, "delete", flag, item["id"], "--force", "--wait-for-state", "TERMINATED")
        for kind, flag in (("security-list", "--security-list-id"), ("dhcp-options", "--dhcp-id")):
            for item in self._children(kind, comp, r.ocid):
                if item["id"] not in defaults:
                    self.oci("network", kind, "delete", flag, item["id"], "--force", "--wait-for-state", "TERMINATED")
        self.oci("network", "vcn", "delete", "--vcn-id", r.ocid, "--force", "--wait-for-state", "TERMINATED")
        self.echo(f"VCN {r.name} deleted")


@dataclass(frozen=True)
class Choice:
    """What the owner picked from the table: an existing VM, or a subnet for a new one."""
    vm: Row | None = None
    subnet_id: str = ""


def review(inv: Inventory, tenancy: str, confirm: Callable[[str], bool],
           ask: Callable[[str, str], str], want_subnet: bool, want_vm: bool = True) -> Choice:
    """The interactive part of onboarding."""
    if not confirm("Do you want to check the existing compartments, VCNs, subnets and VMs?"):
        return Choice()
    rows = inv.rows(tenancy)
    inv.show(rows)
    if rows and confirm("Do you want to delete any of them?"):
        answer = ask("S.No or OCIDs to delete, comma separated", "")
        chosen, unknown = inv.select(rows, answer)
        if unknown:
            inv.echo(f"Not in the table, ignored: {', '.join(unknown)}")
        ignore: frozenset[str] = frozenset()
        for r in chosen:
            if r.kind == "VM":
                ignore |= inv.vm_vnics(r.ocid)
        deletable = []
        for r in chosen:
            also, blockers = inv.dependencies(r, ignore)
            inv.echo(f"{r.no}. {r.kind} {r.name} ({r.ocid})")
            for a in also:
                label = "kept" if a.endswith("detached and kept") else "also deleted"
                inv.echo(f"     {label}: {a}")
            if blockers:
                for b in blockers:
                    inv.echo(f"     still in use: {b}")
                inv.echo("     -> blocked: it stays until what uses it is removed")
            else:
                inv.echo("     -> nothing uses it")
                deletable.append(r)
        if deletable:
            names = ", ".join(f"{r.no}. {r.kind} {r.name}" for r in deletable)
            vms = [r for r in deletable if r.kind == "VM"]
            if not confirm(f"Delete these now: {names}? This cannot be undone"):
                inv.echo("Nothing deleted")
            elif any(ask(f"Type the VM name to terminate it ({r.name})", "").strip() != r.name for r in vms):
                inv.echo("A VM name did not match: nothing deleted")
            else:
                inv.delete(deletable)
                rows = inv.rows(tenancy)
                inv.show(rows)
        elif chosen:
            inv.echo("Nothing can be deleted: every choice is still in use")
    vms = [r for r in rows if r.kind == "VM" and r.state == "RUNNING" and r.public]
    if want_vm and vms:
        answer = ask("S.No of an existing VM to install VASH on (Enter = create a new VM)", "").strip()
        if answer:
            chosen, _ = inv.select(vms, answer)
            if chosen:
                return Choice(vm=chosen[0])
            inv.echo(f"{answer} is not a running VM with a public IP in the table; a new VM will be created")
    if not want_subnet:
        return Choice()
    public = [r for r in rows if r.kind == "Subnet" and r.public == "yes" and r.state == "AVAILABLE"]
    if not public:
        return Choice()
    answer = ask("S.No of a public subnet for the VASH VM (Enter = create a new network)", "").strip()
    if not answer:
        return Choice()
    chosen, _ = inv.select(public, answer)
    if not chosen:
        inv.echo(f"{answer} is not a public subnet in the table; a new network will be created")
        return Choice()
    return Choice(subnet_id=chosen[0].ocid)
