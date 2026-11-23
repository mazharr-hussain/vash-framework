"""Mask before text leaves the VM, gate what is left, unmask the answers on the VM."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .detectors import pattern_hits, person_hits, secret_hits

PLACEHOLDER = re.compile(r"<(?:[A-Z_]+)_\d+>")


@dataclass(frozen=True)
class Finding:
    kind: str
    start: int
    end: int


@dataclass
class Masker:
    CODE_SUFFIXES = (".pks", ".pkb", ".sql", ".apexlang", ".py", ".java", ".js", ".ts", ".tf", ".sh", ".json",
                     ".yml", ".yaml", ".xml", ".css")

    """One masker per job: the same value always gets the same placeholder, across all the pieces of the job."""

    terms: list[str] = field(default_factory=list)  # the owner's client terms (names, domains, hosts ...)
    prose: bool = True  # people's names are looked for in documents only, not in code
    mapping: dict[str, str] = field(default_factory=dict)  # placeholder -> value; never leaves the VM
    _by_value: dict[tuple[str, str], str] = field(default_factory=dict)

    @classmethod
    def is_prose(cls, name: str) -> bool:
        return not name.lower().endswith(cls.CODE_SUFFIXES)

    @classmethod
    def from_file(cls, path: Path) -> "Masker":
        """The owner's terms, one per line (# comments allowed)."""
        terms = []
        if path.exists():
            terms = [t.strip() for t in path.read_text().splitlines() if t.strip() and not t.startswith("#")]
        return cls(terms=terms)

    def _placeholder(self, kind: str, value: str) -> str:
        key = (kind, value.lower() if kind == "TERM" else value)
        if key not in self._by_value:
            n = sum(1 for k in self._by_value if k[0] == kind) + 1
            name = f"<{kind}_{n}>"
            self._by_value[key] = name
            self.mapping[name] = value
        return self._by_value[key]

    def spans(self, text: str) -> list[tuple[int, int, str]]:
        found: list[tuple[int, int, str]] = []
        for term in sorted(self.terms, key=len, reverse=True):  # longest first, case-insensitive, whole words
            for m in re.finditer(rf"(?i)(?<!\w){re.escape(term)}(?!\w)", text):
                found.append((m.start(), m.end(), "TERM"))
        found += list(pattern_hits(text)) + list(secret_hits(text))
        if self.prose:
            found += list(person_hits(text))
        found.sort(key=lambda s: (s[0], -(s[1] - s[0])))
        merged: list[tuple[int, int, str]] = []
        for s in found:  # keep the first, longest span where spans overlap
            if not merged or s[0] >= merged[-1][1]:
                merged.append(s)
        return merged

    def mask(self, text: str) -> str:
        out, last = [], 0
        for start, end, kind in self.spans(text):
            out.append(text[last:start])
            out.append(self._placeholder(kind, text[start:end]))
            last = end
        out.append(text[last:])
        return "".join(out)

    def save(self, path: Path) -> None:
        """The map stays on the VM, readable by its owner only."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(self.mapping, f, indent=1)


def gate(masked: str, terms: list[str] | None = None, prose: bool = True) -> list[Finding]:
    """What is still sensitive after masking (placeholders are fine). Empty: the text may leave the VM."""
    probe = Masker(terms=list(terms or []), prose=prose)
    return [Finding(kind, s, e) for s, e, kind in probe.spans(masked)
            if not PLACEHOLDER.search(masked[s:e])]


def unmask(text: str, mapping: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)
