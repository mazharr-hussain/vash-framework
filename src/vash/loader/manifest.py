"""Generates ai-manifest.json from catalog entries."""
import json
import warnings
from pathlib import Path
from typing import Any
import jsonschema
from vash.core.paths import vash_root

ENTRY_FIELDS = ("id", "type", "source", "fork", "licence", "use", "version", "commit", "stacks", "adr", "search_log", "status")
def _parse_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    block = text[4:end]
    data = {}
    for line in block.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            val = v.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                val = [x.strip() for x in inner.split(",")] if inner else []
            data[k.strip()] = val
    return data

def generate_manifest(repo_root: Path) -> dict[str, Any]:
    """Scan the catalog and build the manifest."""
    catalog = vash_root() / "catalog"
    entries = []

    licences: list[str] = []
    lic_path = catalog / "licences.json"
    if lic_path.exists():
        try:
            lic_data = json.loads(lic_path.read_text(encoding="utf-8"))
            licences = lic_data.get("licences_allowed", [])
        except Exception:
            pass

    schema_path = vash_root() / "method" / "schemas" / "ai-manifest.schema.json"
    validator = None
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)

    if catalog.exists():
        for path in catalog.rglob("*.md"):
            if path.name == "README.md" or path.name == "SKILL.md":
                continue
            meta = _parse_frontmatter(path)
            if meta and "id" in meta:
                meta = {k: v for k, v in meta.items() if k in ENTRY_FIELDS}
                if validator:
                    try:
                        draft = {
                            "schema_version": "1.0",
                            "licences_allowed": licences,
                            "entries": [meta]
                        }
                        validator.validate(draft)
                    except jsonschema.ValidationError as e:
                        warnings.warn(f"Skipping invalid manifest entry {path}: {e.message}")
                        continue
                entries.append(meta)

    return {
        "schema_version": "1.0",
        "licences_allowed": licences,
        "entries": entries
    }
