from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Paper:
    title: str
    authors: list[str]
    year: int
    abstract: str
    doi: str = ""
    citations: int = 0
    source: str = ""

    @property
    def citation_key(self) -> str:
        first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
        return f"{first_author}{self.year}"
