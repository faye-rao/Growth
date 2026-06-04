"""In-memory experience registry with a publish lifecycle.

Operations register experiences as drafts, then ``publish`` them to make them
eligible for delivery (``ExperienceService`` gates on ``status == published``).
``pause`` takes a live experience back out of delivery without deleting it.
"""
from __future__ import annotations

from typing import Dict, List

from .models import PAUSED, PUBLISHED, Experience


class ExperienceStore:
    """A keyed registry of :class:`Experience` objects."""

    def __init__(self) -> None:
        self._by_key: Dict[str, Experience] = {}

    def register(self, experience: Experience) -> Experience:
        """Register (or replace) an experience under its key."""
        self._by_key[experience.key] = experience
        return experience

    def get(self, key: str) -> Experience | None:
        """Return the experience for ``key`` or ``None`` if not registered."""
        return self._by_key.get(key)

    def publish(self, key: str) -> Experience:
        """Flip an experience to ``published`` so it becomes deliverable."""
        exp = self._require(key)
        exp.status = PUBLISHED
        return exp

    def pause(self, key: str) -> Experience:
        """Take a live experience out of delivery (back to ``paused``)."""
        exp = self._require(key)
        exp.status = PAUSED
        return exp

    def list_published(self) -> List[Experience]:
        """Return all currently published experiences (registration order)."""
        return [e for e in self._by_key.values() if e.is_published]

    def _require(self, key: str) -> Experience:
        exp = self._by_key.get(key)
        if exp is None:
            raise KeyError(f"experience {key!r} is not registered")
        return exp


__all__ = ["ExperienceStore"]
