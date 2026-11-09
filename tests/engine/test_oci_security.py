from vash.adapters.cloud.oci.security import VaultSetup

TEN = "ocid1.tenancy..t"


class FakeOci:
    def __init__(self, vaults=None, keys=None, comps=None):
        self.calls = []
        self.vaults = vaults or {}  # compartment id -> [vault dict]
        self.keys = keys or []
        self.comps = comps if comps is not None else [{"id": "ocid1.comp..app", "name": "APP"}]

    def __call__(self, *args):
        self.calls.append(args)
        a = list(args)
        if a[:3] == ["iam", "compartment", "list"]:
            if "--name" in a:
                name = a[a.index("--name") + 1]
                return {"data": [c for c in self.comps if c["name"] == name]}
            return {"data": self.comps}
        if a[:3] == ["iam", "compartment", "create"]:
            return {"data": {"id": "ocid1.comp..sec"}}
        if a[:3] == ["iam", "compartment", "get"]:
            return {"data": {"lifecycle-state": "ACTIVE"}}
        if a[:4] == ["kms", "management", "vault", "list"]:
            return {"data": self.vaults.get(a[a.index("--compartment-id") + 1], [])}
        if a[:4] == ["kms", "management", "vault", "create"]:
            return {"data": {"id": "ocid1.vault..new", "management-endpoint": "https://new-management"}}
        if a[:4] == ["kms", "management", "key", "list"]:
            return {"data": self.keys}
        if a[:4] == ["kms", "management", "key", "create"]:
            return {"data": {"id": "ocid1.key..new"}}
        return {}


def lines():
    out = []
    return out, out.append


VAULT = {"id": "ocid1.vault..v", "display-name": "security-vault", "vault-type": "DEFAULT",
         "lifecycle-state": "ACTIVE", "management-endpoint": "https://v-management"}


def test_existing_vault_and_key_are_listed_and_picked_by_number():
    fake = FakeOci(vaults={"ocid1.comp..app": [VAULT]},
                   keys=[{"display-name": "master", "id": "ocid1.key..m", "lifecycle-state": "ENABLED"}])
    out, echo = lines()
    answers = iter(["1", "1"])
    chosen = VaultSetup(fake, echo, lambda q: True, lambda q, d: next(answers)).choose(TEN, "vash-secrets-key")
    assert chosen == {"vault_id": "ocid1.vault..v", "vault_endpoint": "https://v-management",
                      "key_id": "ocid1.key..m", "vault_compartment_id": "ocid1.comp..app"}
    assert any("security-vault" in line and "virtual (free)" in line and "master" in line for line in out)
    assert not any(c[:2] == ("kms", "management") and c[3] == "create" for c in fake.calls)


def test_enter_creates_vault_in_default_security_compartment_and_a_key():
    fake = FakeOci(vaults={"ocid1.comp..app": [VAULT]})
    asked = []
    def confirm(q):
        asked.append(q)
        return True
    chosen = VaultSetup(fake, lambda m: None, confirm, lambda q, d: "").choose(TEN, "vash-secrets-key")
    assert chosen["vault_id"] == "ocid1.vault..new" and chosen["key_id"] == "ocid1.key..new"
    assert chosen["vault_compartment_id"] == "ocid1.comp..sec"
    create = next(c for c in fake.calls if c[:3] == ("iam", "compartment", "create"))
    assert create[create.index("--name") + 1] == "security"
    vault = next(c for c in fake.calls if c[:4] == ("kms", "management", "vault", "create"))
    assert vault[vault.index("--vault-type") + 1] == "DEFAULT" and "security-vault" in vault
    key = next(c for c in fake.calls if c[:4] == ("kms", "management", "key", "create"))
    assert key[key.index("--endpoint") + 1] == "https://new-management" and "vash-secrets-key" in key
    assert any("Create it?" in q for q in asked)  # a new compartment needs its own yes


def test_owner_names_the_security_compartment_and_an_existing_one_is_reused():
    fake = FakeOci(comps=[{"id": "ocid1.comp..kms", "name": "Shared-Keys"}])
    answers = iter(["bad name!", "Shared-Keys"])
    out, echo = lines()
    chosen = VaultSetup(fake, echo, lambda q: "named 'security'" not in q,
                        lambda q, d: next(answers)).choose(TEN, "north-secrets-key")
    assert chosen["vault_compartment_id"] == "ocid1.comp..kms"
    assert not any(c[:3] == ("iam", "compartment", "create") for c in fake.calls)
    assert any("Please type a name" in line for line in out)


def test_wrong_vault_number_is_asked_again():
    fake = FakeOci(vaults={"ocid1.comp..app": [VAULT]},
                   keys=[{"display-name": "master", "id": "ocid1.key..m", "lifecycle-state": "ENABLED"}])
    out, echo = lines()
    answers = iter(["7", "1", "1"])
    chosen = VaultSetup(fake, echo, lambda q: True, lambda q, d: next(answers)).choose(TEN, "k")
    assert chosen["vault_id"] == "ocid1.vault..v"
    assert any("'7' is not a valid choice" in line for line in out)
