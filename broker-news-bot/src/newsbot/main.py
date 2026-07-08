from __future__ import annotations

from dotenv import load_dotenv

from .config import Settings
from .emailer import send_digest
from .fetcher import fetch_articles


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    settings.validate()

    candidates = fetch_articles(settings.lookback_hours)[: settings.max_articles]
    send_digest(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        email_from=settings.email_from,
        email_to=settings.email_to,
        articles=candidates,
    )


if __name__ == "__main__":
    main()
