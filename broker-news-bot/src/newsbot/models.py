from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    source: str
    published_at: datetime | None
    summary: str
