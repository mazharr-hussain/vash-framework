"""Deterministic detectors of sensitive values (no AI): patterns, checksums and detect-secrets' specific plugins."""
from __future__ import annotations

import re
from typing import Callable, Iterator

Detector = Callable[[str], Iterator[tuple[int, int, str]]]  # (start, end, kind)


def _iban_ok(value: str) -> bool:
    s = re.sub(r"\s+", "", value).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", s):
        return False
    digits = "".join(str(int(c, 36)) for c in s[4:] + s[:4])
    return int(digits) % 97 == 1


def _luhn_ok(value: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", value)][::-1]
    if not 13 <= len(d) <= 19:
        return False
    return sum(x if i % 2 == 0 else (x * 2 - 9 if x * 2 > 9 else x * 2) for i, x in enumerate(d)) % 10 == 0


PATTERNS: list[tuple[str, re.Pattern[str], Callable[[str], bool] | None]] = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), None),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}(?:[ ]?[A-Z0-9]{1,4})?\b"), _iban_ok),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b"), _luhn_ok),
    ("OCID", re.compile(r"\bocid1\.[a-z0-9]+\.[a-z0-9-]*\.[a-z0-9-]*\.[a-z0-9]{20,}\b"), None),
    ("IP", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
     lambda v: not v.startswith(("0.", "127.", "255.")) and v not in ("1.0.0.0",)),
    # National identity numbers: 10 digits starting with 1 or 2 (Saudi national ID / Iqama), standing alone.
    ("NATIONAL_ID", re.compile(r"(?<![\d.])[12]\d{9}(?![\d.])"), None),
    ("PHONE", re.compile(r"(?<![\w.])(?:\+|00)\d[\d ()-]{7,16}\d(?!\w)"), None),
]


def pattern_hits(text: str) -> Iterator[tuple[int, int, str]]:
    for kind, rx, check in PATTERNS:
        for m in rx.finditer(text):
            if check is None or check(m.group(0)):
                yield m.start(), m.end(), kind


# detect-secrets' plugins for specific secret formats; the entropy plugins flag ordinary code, so they are left out.
SECRET_PLUGINS = [
    "AWSKeyDetector", "ArtifactoryDetector", "AzureStorageKeyDetector", "BasicAuthDetector", "CloudantDetector",
    "DiscordBotTokenDetector", "GitHubTokenDetector", "GitLabTokenDetector", "IbmCloudIamDetector",
    "IbmCosHmacDetector", "JwtTokenDetector", "KeywordDetector", "MailchimpDetector", "NpmDetector",
    "OpenAIDetector", "PrivateKeyDetector", "PypiTokenDetector", "SendGridDetector", "SlackDetector",
    "SoftlayerDetector", "SquareOAuthDetector", "StripeDetector", "TelegramBotTokenDetector", "TwilioKeyDetector",
]


def secret_hits(text: str) -> Iterator[tuple[int, int, str]]:
    try:
        from detect_secrets.core.scan import scan_line
        from detect_secrets.settings import transient_settings
    except ImportError:  # without detect-secrets the gate still blocks on the keyword pattern below
        for m in re.compile(r"(?i)(?:password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?([^\s'\",;]{4,})").finditer(text):
            yield m.start(1), m.end(1), "SECRET"
        return
    offset = 0
    with transient_settings({"plugins_used": [{"name": n} for n in SECRET_PLUGINS]}):
        for line in text.splitlines(keepends=True):
            for s in scan_line(line):
                value = s.secret_value or ""
                if len(value) >= 4:
                    i = line.find(value)
                    if i >= 0:
                        yield offset + i, offset + i + len(value), "SECRET"
            offset += len(line)


_ANALYZER = None
PERSON_SCORE = 0.6
NAME_WORD = re.compile(r"[A-Z][a-z]+(?:[-'][A-Z]?[a-z]+)?")
# Words that make a phrase a role, a team or a thing, not a person (the small English model often thinks otherwise).
NOT_NAMES = {
    "account", "admin", "administrator", "agent", "alert", "analyst", "app", "application", "approver", "bank",
    "board", "branch", "case", "checker", "client", "committee", "compliance", "customer", "data", "department",
    "desk", "director", "document", "engine", "file", "flow", "form", "group", "head", "kyc", "lead", "level",
    "maker", "manager", "member", "officer", "operations", "owner", "page", "party", "portal", "process", "product",
    "queue", "report", "request", "review", "reviewer", "risk", "role", "screen", "service", "status", "step",
    "system", "task", "team", "test", "user", "workflow",
}


def person_hits(text: str) -> Iterator[tuple[int, int, str]]:
    """People's names, by Microsoft Presidio with spaCy's small English model (installed on the VM; when absent,
    names are masked only through the owner's list of terms)."""
    global _ANALYZER
    if _ANALYZER is None:
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            nlp = NlpEngineProvider(nlp_configuration={
                "nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]}).create_engine()
            _ANALYZER = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
        except Exception:  # not installed here: names fall back to the owner's terms
            _ANALYZER = False
    if not _ANALYZER:
        return
    for r in _ANALYZER.analyze(text=text, language="en", entities=["PERSON"]):
        if r.score < PERSON_SCORE:
            continue
        words = text[r.start:r.end].split()
        # A leading role word ("Customer Ahmed Khan") is not part of the name.
        while words and words[0].lower() in NOT_NAMES:
            r.start += text[r.start:r.end].find(words[1]) if len(words) > 1 else 0
            words = words[1:]
        if 2 <= len(words) <= 4 and all(NAME_WORD.fullmatch(w) for w in words) \
                and not any(w.lower() in NOT_NAMES for w in words):
            yield r.start, r.start + len(" ".join(words)), "PERSON"


def names_available() -> bool:
    """Whether people's names are detected here (Presidio installed)."""
    list(person_hits("Sara Ali"))
    return bool(_ANALYZER)
