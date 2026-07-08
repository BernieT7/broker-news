from __future__ import annotations

import smtplib
from datetime import datetime
from email.message import EmailMessage

from .models import Article


def send_digest(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    email_from: str,
    email_to: list[str],
    articles: list[Article],
) -> None:
    message = EmailMessage()
    today = datetime.now().strftime("%Y-%m-%d")
    message["Subject"] = f"券商策略新聞重點｜{today}"
    message["From"] = email_from
    message["To"] = ", ".join(email_to)
    message.set_content(_plain_text(articles))
    message.add_alternative(_html(articles), subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)


def _plain_text(articles: list[Article]) -> str:
    if not articles:
        return "今天沒有找到符合條件的重大券商策略新聞。"

    lines = ["今日券商策略候選新聞：", ""]
    for index, article in enumerate(articles, 1):
        published = article.published_at.strftime("%Y-%m-%d %H:%M") if article.published_at else "時間未知"
        lines.extend(
            [
                f"{index}. {article.title}",
                f"來源：{article.source}｜時間：{published}",
                f"摘要：{article.summary}" if article.summary else "摘要：無",
                f"連結：{article.url}",
                "",
            ]
        )
    return "\n".join(lines)


def _html(articles: list[Article]) -> str:
    if not articles:
        return "<p>今天沒有找到符合條件的重大券商策略新聞。</p>"

    items = []
    for article in articles:
        published = article.published_at.strftime("%Y-%m-%d %H:%M") if article.published_at else "時間未知"
        items.append(
            f"""
            <li>
              <h3><a href="{article.url}">{article.title}</a></h3>
              <p><strong>來源：</strong>{article.source}｜<strong>時間：</strong>{published}</p>
              <p><strong>摘要：</strong>{article.summary or "無"}</p>
            </li>
            """
        )

    return f"""
    <html>
      <body>
        <h2>今日券商策略候選新聞</h2>
        <ol>
          {''.join(items)}
        </ol>
      </body>
    </html>
    """
