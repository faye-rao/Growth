"""Identity resolution — consume the data team's cross-line ID mapping (M8 ours).

We do **not** run a CDP. The data team hands us a mapping of cross-business-line
identifiers (phone, device_id, ...) to a canonical ``customer_id``; we expose a
small resolver over it. No email is ever used (primary key = customer_id / phone).

* ``resolve(identifiers)`` picks the canonical id using the priority
  ``customer_id`` > ``phone`` > ``device_id``, following the data-team mapping.
* ``merge(a, b)`` unions two canonical ids (union-find), so later resolutions of
  either side collapse to one identity.
* ``coverage(inputs)`` reports the fraction of inputs we can resolve — the
  operational signal for "how much of the footprint is identity-resolved".

Zero third-party dependencies (stdlib only).
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

# Resolution priority for a single identifiers dict (no email — by design).
PRIORITY: List[str] = ["customer_id", "phone", "device_id"]

# Identifiers that are themselves primary keys (resolve to self when unmapped).
# Per M8: primary key = customer_id / phone. device_id resolves only via mapping.
PRIMARY_KEYS = {"customer_id", "phone"}

# How a raw identifier field maps into the data-team mapping namespace.
_NAMESPACE = {"phone": "phone", "device_id": "device"}


class IdentityResolver:
    """Resolve cross-line identifiers to one canonical customer_id.

    ``add_mapping("phone:+97150", "u1")`` records a data-team edge; ``merge``
    unions two canonical ids via union-find.
    """

    def __init__(self) -> None:
        # alt-identifier ("phone:+971...", "device:d1") -> canonical customer_id
        self._mapping: Dict[str, str] = {}
        # union-find parent pointers over canonical ids
        self._parent: Dict[str, str] = {}

    # --- union-find -------------------------------------------------------- #
    def _find(self, node: str) -> str:
        self._parent.setdefault(node, node)
        root = node
        while self._parent[root] != root:
            root = self._parent[root]
        # path compression
        while self._parent[node] != root:
            self._parent[node], node = root, self._parent[node]
        return root

    def merge(self, a: str, b: str) -> str:
        """Union two canonical ids; return the surviving representative."""
        ra, rb = self._find(a), self._find(b)
        if ra == rb:
            return ra
        # deterministic: keep the lexicographically smaller root
        root, other = (ra, rb) if ra <= rb else (rb, ra)
        self._parent[other] = root
        return root

    # --- mapping ----------------------------------------------------------- #
    def add_mapping(self, alt_identifier: str, canonical_id: str) -> None:
        """Record a data-team edge: an alt identifier -> a canonical customer_id."""
        self._mapping[alt_identifier] = canonical_id
        self._find(canonical_id)  # register in union-find

    def _canonical(self, value: str) -> str:
        return self._find(value)

    def _lookup_mapped(self, key: str) -> Optional[str]:
        cid = self._mapping.get(key)
        return self._canonical(cid) if cid is not None else None

    # --- resolution -------------------------------------------------------- #
    def resolve(self, identifiers: Dict[str, str]) -> Optional[str]:
        """Resolve a canonical id using priority customer_id > phone > device_id.

        Returns ``None`` if nothing is resolvable.
        """
        for field_name in PRIORITY:
            value = identifiers.get(field_name)
            if not value:
                continue
            if field_name == "customer_id":
                # customer_id is itself a canonical key
                return self._canonical(value)
            mapped = self._lookup_mapped(f"{_NAMESPACE[field_name]}:{value}")
            if mapped is not None:
                return mapped
            # phone is also a primary key (per M8: pk = customer_id / phone), so an
            # unmapped phone resolves to itself; device_id alone is NOT a primary key.
            if field_name in PRIMARY_KEYS:
                return self._canonical(value)
        return None

    def coverage(self, inputs: Iterable[Dict[str, str]]) -> float:
        """Fraction of ``inputs`` that resolve to a canonical id (0.0 if empty)."""
        items = list(inputs)
        if not items:
            return 0.0
        resolved = sum(1 for i in items if self.resolve(i) is not None)
        return resolved / len(items)
