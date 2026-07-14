from __future__ import annotations

import os
from dataclasses import dataclass


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_int_csv(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: list[str]
    lookback_hours: int
    max_articles: int
    retry_delays: list[int]

    @classmethod
    def from_env(cls) -> "Settings":
        max_articles = os.getenv("DIGEST_MAX_ARTICLES") or os.getenv("DIGEST_MAX_CANDIDATES", "10")
        return cls(
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            email_from=os.getenv("EMAIL_FROM", ""),
            email_to=_split_csv(os.getenv("EMAIL_TO", "")),
            lookback_hours=int(os.getenv("DIGEST_LOOKBACK_HOURS", "24")),
            max_articles=int(max_articles),
            retry_delays=_split_int_csv(os.getenv("DIGEST_RETRY_DELAYS", "30,60")),
        )

    def validate(self) -> None:
        missing = []
        for key, value in {
            "SMTP_HOST": self.smtp_host,
            "SMTP_USERNAME": self.smtp_username,
            "SMTP_PASSWORD": self.smtp_password,
            "EMAIL_FROM": self.email_from,
            "EMAIL_TO": ",".join(self.email_to),
        }.items():
            if not value:
                missing.append(key)

        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
