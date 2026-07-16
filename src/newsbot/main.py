from __future__ import annotations

import time

from dotenv import load_dotenv

from .config import Settings
from .emailer import send_digest
from .fetcher import fetch_articles


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    settings.validate()

    candidates = _fetch_with_retries(settings)
    if not candidates:
        print("No candidate articles after retries. Sending the empty digest email.")

    send_digest(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        email_from=settings.email_from,
        email_to=settings.email_to,
        articles=candidates,
    )


def _fetch_with_retries(settings: Settings):
    total_attempts = len(settings.retry_delays) + 1
    for attempt in range(total_attempts):
        if attempt:
            delay = settings.retry_delays[attempt - 1]
            print(f"Retrying after {delay} seconds because the previous attempt found no candidate articles.")
            time.sleep(delay)

        print(f"Fetch attempt {attempt + 1}/{total_attempts}")
        candidates = fetch_articles(settings.lookback_hours)
        print(f"Candidate articles after filtering: {len(candidates)}")
        if candidates:
            return candidates

    return []


if __name__ == "__main__":
    main()
