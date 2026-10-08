from __future__ import annotations

from typing import Protocol

from sqlharness.types import Generation


class SQLGenerator(Protocol):
    def generate(self, *, question: str, evidence: str, schema: str) -> Generation:
        """Generate one SQL candidate from a natural-language request."""

