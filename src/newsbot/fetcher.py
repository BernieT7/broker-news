下面是目前工作區裡最新的 `src/newsbot/fetcher.py`，你可以整段複製：

```python
from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import parse_qs, unquote, urlparse

import feedparser

from .models import Article
from .sources import RSS_SOURCES, NewsSource


HIGH_IMPORTANCE_KEYWORDS = [
    "金管會",
    "證交所",
    "櫃買",
    "交易制度",
    "延長交易",
    "逐筆交易",
    "監理",
    "法規",
    "法規鬆綁",
    "裁罰",
    "改革",
    "investor protection",
    "regulation",
    "regulatory",
    "SEC",
    "FINRA",
    "market structure",
    "retail fraud",
    "fraud working group",
    "enforcement",
    "working group",
    "零股交易",
    "撮合",
    "開盤交易",
]

MEDIUM_IMPORTANCE_KEYWORDS = [
    "Robinhood",
    "Charles Schwab",
    "Futu",
    "SBI",
    "Mirae Asset",
    "Mirai Asset",
    "Samsung Securities",
    "Rakuten Securities",
    "Rakutan Securities",
    "Gemini",
    "wealth management",
    "zero commission",
    "commission-free",
    "super app",
    "mega-IPO",
    "IPO",
    "跨境",
    "複委託",
    "財富管理",
    "AI財富管理",
    "機器人理財",
    "行動下單",
    "APP",
    "布局",
    "佈局",
    "戰略",
    "策略",
]

PURE_MARKETING_KEYWORDS = [
    "回饋",
    "有禮",
    "優惠",
    "抽獎",
    "贈",
    "加碼",
    "限時",
    "活動",
    "campaign",
    "promotion",
    "cashback",
    "reward",
]

STRATEGIC_KEYWORDS = [
    "券商",
    "證券商",
    "證券",
    "金管會",
    "證交所",
    "櫃買",
    "交易制度",
    "延長交易",
    "交割",
    "手續費",
    "複委託",
    "財富管理",
    "成交量",
    "外資",
    "散戶",
    "零股",
    "逐筆交易",
    "監理",
    "法規",
    "裁罰",
    "開放",
    "ai投顧",
    "機器人理財",
    "broker",
    "brokerage",
    "broker-dealer",
    "retail investor",
    "online broker",
    "retail brokerage",
    "wealth management",
    "robo-advisor",
    "broker app",
    "trading app",
    "zero commission",
    "commission",
    "trading volume",
    "market structure",
    "regulation",
    "regulatory",
    "investor protection",
    "SEC",
    "FINRA",
]

BROKERAGE_NAMES = [
    "Robinhood",
    "Charles Schwab",
    "Schwab",
    "Futu",
    "富途",
    "SBI",
    "SBI Securities",
    "Mirae Asset",
    "Mirai Asset",
    "Samsung Securities",
    "Rakuten Securities",
    "Rakutan Securities",
    "樂天證券",
    "元大證券",
    "富邦證券",
    "國泰證券",
    "凱基證券",
    "永豐金證券",
    "群益證券",
]

MACRO_CONTEXT_KEYWORDS = [
    "策略",
    "戰略",
    "佈局",
    "布局",
    "轉型",
    "趨勢",
    "產業",
    "同業",
    "商業模式",
    "行銷",
    "客戶",
    "用戶",
    "開戶",
    "市占",
    "市佔",
    "監理",
    "法規",
    "制度",
    "交易制度",
    "技術",
    "平台",
    "數位",
    "AI",
    "wealth",
    "strategy",
    "strategic",
    "launch",
    "partnership",
    "investment",
    "funding",
    "series c",
    "acquisition",
    "expand",
    "expansion",
    "regulation",
    "regulatory",
    "market structure",
    "industry",
    "trend",
]

NOISE_KEYWORDS = [
    "股價",
    "漲停",
    "跌停",
    "目標價",
    "喊買",
    "喊賣",
    "買進",
    "賣超",
    "買超",
    "EPS",
    "eps",
    "每股盈餘",
    "本益比",
    "殖利率",
    "營收速報",
    "6月營收",
    "月營收",
    "法說",
    "除息",
    "除權",
    "配息",
    "填息",
    "財報",
    "評等",
    "排行",
    "前20名",
    "股市爆料同學會",
    "撿零股",
    "公告注意有價證券",
    "公告處置有價證券",
    "有價證券名單",
    "成交股數前20名",
    "成交量第一",
    "零股成交第一",
    "面板股",
    "0050",
    "00403A",
    "公債",
    "債券等殖",
    "real estate",
    "rumor",
    "spreading rumors",
    "個股",
    "焦點股",
    "台指期",
    "期貨速報",
    "technical analysis",
    "price target",
    "target price",
    "rating",
    "analyst",
    "bullish",
    "bearish",
    "upgrade",
    "downgrade",
    "swot",
    "options",
    "open interest",
    "nasdaq",
    "qqq",
    "etf",
    "debt sells off",
    "earnings",
    "earnings per share",
    "stock rises",
    "stock falls",
    "shares rise",
    "shares fall",
    "buy rating",
]

NOISE_ONLY_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\b\d{4}\b.*股價",
        r"外資.*目標價",
        r"外資.*喊買",
        r"營收.*年增",
        r"營收.*月增",
        r"eps",
        r"price target",
        r"stock (rises|falls|jumps|slides)",
        r"shares (rise|fall|jump|slide)",
        r"analyst target",
        r"options.*contracts",
        r"^\d{4}\s",
        r"成交股數前\d+名",
        r"零股成交.*(ETF|0050|個股|面板股)",
        r"在與券商互動",
        r"買入.*評級",
        r"公告.*債券.*買賣",
    ]
]

HARD_NOISE_KEYWORDS = [
    "rumor",
    "spreading rumors",
]

BROKERAGE_BUSINESS_KEYWORDS = [
    "券商",
    "證券商",
    "複委託",
    "財富管理",
    "零股",
    "交易制度",
    "手續費",
    "開戶",
    "brokerage",
    "broker-dealer",
    "online broker",
    "retail broker",
    "retail brokerage",
    "wealth management",
    "trading app",
    "broker app",
    "zero commission",
    "0% commission",
    "commission-free",
    "super app",
    "customer assets",
    "platform assets",
    "investor protection",
]


def fetch_articles(lookback_hours: int, sources: list[NewsSource] | None = None) -> list[Article]:
    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
    scored_articles: list[tuple[int, Article]] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    seen_title_tokens: list[set[str]] = []
    seen_event_keys: set[str] = set()

    for source in sources or RSS_SOURCES:
        parsed = feedparser.parse(source.url)
        for entry in parsed.entries:
            url = _canonical_url(getattr(entry, "link", "").strip())
            title = _clean_title(getattr(entry, "title", "").strip())
            if not url or not title or url in seen_urls:
                continue

            title_key = _dedupe_key(title)
            event_key = _event_key(title)
            title_tokens = _title_tokens(title)
            if (
                title_key in seen_titles
                or (event_key and event_key in seen_event_keys)
                or _is_near_duplicate(title_tokens, seen_title_tokens)
            ):
                continue

            published_at = _entry_datetime(entry)
            if published_at and published_at < cutoff:
                continue

            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            clean_summary = _clean_summary(summary)
            if not _is_relevant(title, clean_summary):
                continue

            score = _importance_score(title, clean_summary)
            seen_urls.add(url)
            seen_titles.add(title_key)
            if event_key:
                seen_event_keys.add(event_key)
            seen_title_tokens.append(title_tokens)
            scored_articles.append(
                (
                    score,
                    Article(
                        title=title,
                        url=url,
                        source=source.name,
                        published_at=published_at,
                        summary=clean_summary,
                    ),
                )
            )

    scored_articles.sort(
        key=lambda item: (item[0], item[1].published_at or datetime.min.replace(tzinfo=UTC)),
        reverse=True,
    )
    return [article for _, article in scored_articles]


def _entry_datetime(entry: object) -> datetime | None:
    for field in ("published", "updated", "created"):
        value = getattr(entry, field, None)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except (TypeError, ValueError):
            continue
    return None


def _clean_summary(value: str) -> str:
    return _strip_html(value)[:700]


def _clean_title(value: str) -> str:
    return _strip_html(value)


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", unescape(value))
    return " ".join(text.replace("\n", " ").split())


def _canonical_url(url: str) -> str:
    if "news.google.com/rss/articles/" not in url:
        return url

    parsed = urlparse(url)
    query_url = parse_qs(parsed.query).get("url", [""])[0]
    if query_url:
        return unquote(query_url)

    return url.split("?", maxsplit=1)[0]


def _dedupe_key(title: str) -> str:
    normalized = title.lower()
    normalized = re.sub(r"\s*[-|｜]\s*[^-|｜]{1,30}$", "", normalized)
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized)
    return normalized[:90]


def _title_tokens(title: str) -> set[str]:
    normalized = re.sub(r"\s*[-|｜]\s*[^-|｜]{1,30}$", "", title.lower())
    ascii_tokens = set(re.findall(r"[a-z0-9]{3,}", normalized))
    cjk_tokens = set(re.findall(r"[\u4e00-\u9fff]{2}", normalized))
    return ascii_tokens | cjk_tokens


def _is_near_duplicate(tokens: set[str], seen_token_sets: list[set[str]]) -> bool:
    if len(tokens) < 3:
        return False

    for seen_tokens in seen_token_sets:
        overlap = len(tokens & seen_tokens)
        union = len(tokens | seen_tokens)
        if union and overlap / union >= 0.42:
            return True
    return False


def _event_key(title: str) -> str | None:
    lower_title = title.lower()
    if "零股" in title and any(keyword in title for keyword in ["撮合", "9點", "提前", "提早", "開盤"]):
        return "tw_fractional_lot_reform"

    if "gemini" in lower_title and "stock trading" in lower_title and (
        "commission" in lower_title or "commission-free" in lower_title
    ):
        return "gemini_zero_commission_stock_trading"

    if "中國信託證券" in title and "複委託" in title:
        return "ctbc_securities_sub_brokerage_campaign"

    return None


def _is_relevant(title: str, summary: str) -> bool:
    text = f"{title}\n{summary}"
    lower_text = text.lower()

    strategic_hits = _count_hits(lower_text, STRATEGIC_KEYWORDS)
    broker_hits = _count_hits(lower_text, BROKERAGE_NAMES)
    macro_hits = _count_hits(lower_text, MACRO_CONTEXT_KEYWORDS)
    business_hits = _count_hits(lower_text, BROKERAGE_BUSINESS_KEYWORDS)
    hard_noise_hit = any(keyword.lower() in lower_text for keyword in HARD_NOISE_KEYWORDS)
    noise_hit = any(keyword.lower() in lower_text for keyword in NOISE_KEYWORDS) or any(
        pattern.search(text) for pattern in NOISE_ONLY_PATTERNS
    )

    if hard_noise_hit:
        return False

    if _is_pure_marketing(lower_text):
        return False

    if noise_hit and not _has_strong_exception(lower_text):
        return False

    if broker_hits and business_hits:
        return True

    if business_hits and macro_hits:
        return True

    return strategic_hits >= 2 and (macro_hits >= 1 or business_hits >= 1)


def _has_strong_exception(lower_text: str) -> bool:
    return any(
        keyword in lower_text
        for keyword in [
            "金管會",
            "交易制度",
            "延長交易",
            "監理",
            "法規",
            "regulation",
            "regulatory",
            "market structure",
            "investor protection",
        ]
    )


def _is_pure_marketing(lower_text: str) -> bool:
    marketing_hit = any(keyword.lower() in lower_text for keyword in PURE_MARKETING_KEYWORDS)
    if not marketing_hit:
        return False

    return not any(
        keyword in lower_text
        for keyword in [
            "法規",
            "監理",
            "交易制度",
            "market structure",
            "regulation",
            "regulatory",
            "super app",
            "zero commission",
            "commission-free",
            "新功能",
            "全新推出",
            "布局",
            "佈局",
            "戰略",
        ]
    )


def _importance_score(title: str, summary: str) -> int:
    lower_text = f"{title}\n{summary}".lower()
    score = 0

    score += 5 * _count_hits(lower_text, HIGH_IMPORTANCE_KEYWORDS)
    score += 3 * _count_hits(lower_text, MEDIUM_IMPORTANCE_KEYWORDS)
    score += 2 * _count_hits(lower_text, BROKERAGE_BUSINESS_KEYWORDS)

    if "零股" in lower_text and any(keyword in lower_text for keyword in ["交易制度", "撮合", "提前", "提早"]):
        score += 5

    if any(name.lower() in lower_text for name in BROKERAGE_NAMES) and any(
        keyword in lower_text for keyword in ["布局", "佈局", "strategy", "strategic", "launch", "expand"]
    ):
        score += 4

    if any(keyword.lower() in lower_text for keyword in PURE_MARKETING_KEYWORDS):
        score -= 3

    return score


def _count_hits(lower_text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword.lower() in lower_text)
```
