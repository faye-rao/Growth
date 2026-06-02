"""NL2SQL — natural-language → rule DSL (M2-B1~B4).

A *deterministic, template/slot-based* translator (no external LLM): it splits an
utterance into clauses, matches each clause against an ordered library of intent
templates, and composes a rule DSL. This is the MVP fallback path that guarantees
predictable accuracy on the high-frequency phrasings (B4 template-first), reports a
confidence score and flags low-confidence output for human review (B3), and always
returns the generated DSL transparently so it can be previewed/edited (B2).

A future iteration can put an LLM in front (schema-linking) and keep this layer as
the deterministic fallback / validator.

Supported grammar (canonical phrasings) — see README "NL2SQL grammar".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# --- lexicons -----------------------------------------------------------------
_COUNTRY_NAMES = {
    "uae": "AE", "emirates": "AE", "india": "IN", "philippines": "PH",
    "pakistan": "PK", "egypt": "EG",
}
_EVENTS = {
    "logout": "User Logout", "logged out": "User Logout", "log out": "User Logout",
    "transfer": "Transfer", "transferred": "Transfer", "remittance": "Transfer",
    "app open": "App Opened", "opened the app": "App Opened", "opened app": "App Opened",
    "push register": "Push ID Register Android", "registered push": "Push ID Register Android",
}
_NEGATIONS = ("not ", "no ", "haven't ", "hasn't ", "have not ", "has not ",
              "without ", "don't ", "didn't ", "never ")

_GTE_WORDS = ("over", "above", "greater than", "more than", "at least", ">=", ">")
_LTE_WORDS = ("under", "below", "less than", "fewer than", "at most", "<=", "<")
_EQ_WORDS = ("exactly", "equal to", "equals", "is", "=")


@dataclass
class NL2SQLResult:
    text: str
    dsl: Dict[str, Any]               # {"match": <node>} — editable preview (B2)
    confidence: float                 # matched_clauses / total_clauses (B3)
    matched: List[str] = field(default_factory=list)
    unmatched: List[str] = field(default_factory=list)
    requires_review: bool = False     # True when confidence < threshold (B3)


REVIEW_THRESHOLD = 1.0  # any unmatched clause -> flag for human review


def translate(text: str, *, threshold: float = REVIEW_THRESHOLD) -> NL2SQLResult:
    raw = text.strip()
    connector, clauses = _split_clauses(raw)

    nodes: List[Dict[str, Any]] = []
    matched: List[str] = []
    unmatched: List[str] = []
    for clause in clauses:
        node = _match_clause(clause)
        if node is None:
            unmatched.append(clause)
        else:
            nodes.append(node)
            matched.append(clause)

    if not nodes:
        match_node: Dict[str, Any] = {"op": "and", "children": []}
    elif len(nodes) == 1:
        match_node = nodes[0]
    else:
        match_node = {"op": connector, "children": nodes}

    total = len(clauses) if clauses else 1
    confidence = round(len(matched) / total, 3)
    return NL2SQLResult(
        text=raw,
        dsl={"match": match_node},
        confidence=confidence,
        matched=matched,
        unmatched=unmatched,
        requires_review=confidence < threshold,
    )


# --- clause splitting ---------------------------------------------------------
def _split_clauses(text: str) -> Tuple[str, List[str]]:
    low = text.lower()
    # strip a leading "users who/that/with" preamble per whole sentence later per-clause
    if " or " in low and " and " not in low:
        connector = "or"
        parts = re.split(r"\bor\b", low)
    else:
        connector = "and"
        parts = re.split(r"\band\b|[,，;；]", low)
    clauses = [p.strip(" .\t") for p in parts if p.strip(" .\t")]
    return connector, clauses


# --- per-clause matching ------------------------------------------------------
def _strip_preamble(clause: str) -> Tuple[str, bool]:
    """Remove 'users who/that/with' preamble; return (clause, negated)."""
    c = clause
    for pre in ("users who ", "users that ", "users with ", "users ", "who ", "that ", "with "):
        if c.startswith(pre):
            c = c[len(pre):]
            break
    negated = False
    for neg in _NEGATIONS:
        if c.startswith(neg) or f" {neg}" in f" {c}":
            negated = True
            # remove the first negation token to ease downstream matching
            c = re.sub(r"^(not|no|haven't|hasn't|have not|has not|without|don't|didn't|never)\s+",
                       "", c, count=1)
            break
    return c.strip(), negated


def _match_clause(clause: str) -> Optional[Dict[str, Any]]:
    """Collect every condition recognized in the clause and AND them together.

    A single clause may carry multiple conditions (e.g. "KYC users with balance
    over 1000"), so we run all matchers rather than first-wins.
    """
    c, negated = _strip_preamble(clause)
    hits: List[Dict[str, Any]] = []
    for matcher in (_m_kyc, _m_wallet, _m_platform, _m_balance, _m_country, _m_event):
        node = matcher(c, negated)
        if node is not None:
            hits.append(node)
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    return {"op": "and", "children": hits}


def _attr(field_: str, operator: str, value: Any) -> Dict[str, Any]:
    return {"type": "attribute", "field": field_, "operator": operator, "value": value}


def _maybe_not(node: Dict[str, Any], negated: bool) -> Dict[str, Any]:
    return {"op": "not", "children": [node]} if negated else node


def _m_kyc(c: str, negated: bool) -> Optional[Dict[str, Any]]:
    if "kyc" in c or "verified" in c:
        # "unverified" already had its 'un' inside; treat 'verified'+negated as false
        value = not negated
        if "unverified" in c:
            value = False
        return _attr("is_kyc", "eq", value)
    return None


def _m_wallet(c: str, negated: bool) -> Optional[Dict[str, Any]]:
    if "wallet" in c and ("activ" in c):
        return _attr("wallet_activated", "eq", not negated)
    return None


def _m_platform(c: str, negated: bool) -> Optional[Dict[str, Any]]:
    if re.search(r"\bandroid\b", c):
        return _attr("platform", "ne" if negated else "eq", "Android")
    if re.search(r"\bios\b", c):
        return _attr("platform", "ne" if negated else "eq", "iOS")
    return None


def _m_balance(c: str, negated: bool) -> Optional[Dict[str, Any]]:
    if "balance" not in c:
        return None
    num = _first_number(c)
    if num is None:
        return None
    if any(w in c for w in _LTE_WORDS):
        op = "lte"
    elif any(w in c for w in _GTE_WORDS):
        op = "gte"
    elif any(w in c for w in _EQ_WORDS):
        op = "eq"
    else:
        op = "gte"  # sensible default for "balance 1000"
    return _attr("balance", op, num)


def _m_country(c: str, negated: bool) -> Optional[Dict[str, Any]]:
    # country name
    for name, code in _COUNTRY_NAMES.items():
        if re.search(rf"\b{name}\b", c):
            return _attr("country", "not_in" if negated else "in", [code])
    # explicit 2-letter code after in/from/country
    m = re.search(r"\b(?:in|from|country(?:\s+is)?)\s+([a-z]{2})\b", c)
    if m:
        return _attr("country", "not_in" if negated else "in", [m.group(1).upper()])
    return None


def _m_event(c: str, negated: bool) -> Optional[Dict[str, Any]]:
    event = None
    for kw, name in _EVENTS.items():
        if kw in c:
            event = name
            break
    if event is None:
        return None

    within = None
    mw = re.search(r"(?:last|past|within|in the last)\s+(\d+)\s*day", c)
    if mw:
        within = int(mw.group(1))

    # frequency: "at least N times" / "N times" -> at_least N ; default at_least 1
    times = re.search(r"at least\s+(\d+)\s*time", c) or re.search(r"(\d+)\s*time", c)
    n = int(times.group(1)) if times else 1
    cond: Dict[str, Any] = {
        "type": "event", "event": event,
        "frequency": {"op": "at_least", "value": n},
    }
    if within is not None:
        cond["within_days"] = within
    return _maybe_not(cond, negated)


def _first_number(c: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)", c)
    if not m:
        return None
    v = float(m.group(1))
    return int(v) if v.is_integer() else v
