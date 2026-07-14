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
    "交易制度",
    "延長交易",
    "逐筆交易",
    "監理",
    "法規",
    "法規鬆綁",
    "裁罰",
    "改革",
    "market design",
    "investor protection",
    "regulation",
    "regulatory",
    "enforcement",
    "tokenization",
    "tokenized securities",
    "digital securities",
    "RWA",
    "securities token",
    "AI",
]

MEDIUM_IMPORTANCE_KEYWORDS = [
    "證交所",
    "金管會",
    "櫃買",
    "SEC",
    "FINRA",
    "ESMA",
    "Robinhood",
    "Charles Schwab",
    "IBKR",
    "Interactive broker",
    "Futu",
    "SBI",
    "Mirae Asset",
    "Samsung Securities",
    "Rakuten Securities",
    "Gemini",
    "zero commission",
    "commission-free",
    "super app",
    "跨境",
    "機器人理財",
    "行動下單",
    "APP",
    "布局",
    "佈局",
    "戰略",
    "複委託",
    "T+1",
    "T+2",
    "central counterparty",
    "post trade",
    "margin",
    "clearing",
    "settlement",
    "策略",
    "零股交易",
    "撮合",
    "開盤交易",
    "金融科技",
    "fintech",
    "web3",
    "RWA",
    "crypto",
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
    "爆料",
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
    "retail investing",
    "online broker",
    "digital brokerage",
    "online brokerage",
    "retail brokerage",
    "robo-advisor",
    "broker ecosystem",
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
    "零股交易",
    "撮合",
    "開盤交易",
    "金融科技",
    "fintech",
    "web3",
    "RWA",
    "crypto",
    "mega-IPO",
    "IPO",
]

BROKERAGE_NAMES = [
    "Robinhood",
    "Charles Schwab",
    "Schwab",
    "IBKR",
    "Interactive broker",
    "Futu",
    "富途",
    "SBI",
    "SBI Securities",
    "Mirae Asset",
    "Samsung Securities",
    "Rakuten Securities",
    "Trade Republic",
    "Scalable Capital",
    "Saxo Bank",
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
    "web3",
    "RWA",
]

HARD_EXCLUDE_KEYWORDS = [
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
    "top stocks",
    "stock picks",
    "dividend stocks",
    "dividend yield",
    "price prediction",
    "portfolio picks",
    "bullish",
    "bearish",
    "upgrade",
    "downgrade",
    "swot",
    "open interest",
    "未平倉",
    "qqq",
    "debt sells off",
    "earnings per share",
    "stock rises",
    "stock falls",
    "shares rise",
    "shares fall",
    "buy rating",
    "etf配息",
    "ETF配息",
    "ETF 淨值",
    "ETF淨值",
    "ETF成分股",
    "ETF 成分股",
    "成分股調整",
    "配息公告",
    "爆料",
]

HARD_EXCLUDE_PATTERNS = [
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
        r"how to buy",
        r"should you buy",
        r"top .*stocks",
        r"price prediction",
        r"dividend (stocks|yield|income)",
        r"ETF.*(淨值|配息|成分股)",
        r"etf.*(holdings|constituents|distribution|dividend)",
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

SOFT_NOISE_GROUPS = [
    (["etf", "ETF"], 1),
    (["options", "option contracts", "open interest"], 1),
    (["earnings", "quarterly results"], 2),
    (["analyst", "rating", "upgrade", "downgrade"], 2),
    (["nasdaq", "NASDAQ", "futures", "期貨"], 1),
]

BROKERAGE_BUSINESS_KEYWORDS = [
    "券商",
    "證券商",
    "複委託",
    "零股",
    "交易制度",
    "手續費",
    "開戶",
    "brokerage",
    "broker-dealer",
    "online broker",
    "retail broker",
    "retail brokerage",
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

TOPIC_GROUPS = [
    (
        "regulation",
        12,
        [
            "金管會",
            "監理",
            "法規",
            "法規鬆綁",
            "裁罰",
            "SEC",
            "FINRA",
            "ESMA",
            "investor protection",
            "regulation",
            "regulatory",
            "enforcement",
            "digital securities",
            "tokenized securities",
        ],
    ),
    (
        "market_structure",
        10,
        [
            "證交所",
            "櫃買",
            "交易制度",
            "延長交易",
            "逐筆交易",
            "零股",
            "零股交易",
            "撮合",
            "開盤交易",
            "market structure",
            "market design",
            "T+1",
            "T+2",
            "clearing",
            "settlement",
            "central counterparty",
            "post trade",
            "DTCC",
        ],
    ),
    (
        "broker_strategy",
        8,
        BROKERAGE_NAMES
        + [
            "跨境",
            "複委託",
            "布局",
            "佈局",
            "戰略",
            "策略",
            "acquisition",
            "expand",
            "expansion",
            "partnership",
            "investment",
            "funding",
            "series c",
            "mega-IPO",
            "IPO",
        ],
    ),
    (
        "product_innovation",
        6,
        [
            "行動下單",
            "APP",
            "trading app",
            "broker app",
            "zero commission",
            "0% commission",
            "commission-free",
            "super app",
            "options trading",
            "launch",
            "推出",
            "新功能",
            "全新推出",
        ],
    ),
    (
        "fintech_ai_rwa",
        6,
        [
            "金融科技",
            "fintech",
            "AI",
            "ai投顧",
            "機器人理財",
            "web3",
            "RWA",
            "crypto",
            "tokenization",
            "tokenized securities",
            "digital securities",
            "securities token",
        ],
    ),
]

WEALTH_MANAGEMENT_KEYWORDS = [
    "財富管理",
    "wealth management",
    "wealth",
    "robo-advisor",
    "AI財富管理",
    "機器人理財",
    "customer assets",
    "platform assets",
]

CORE_FOCUS_KEYWORDS = [
    "金管會",
    "證交所",
    "櫃買",
    "交易制度",
    "延長交易",
    "逐筆交易",
    "零股",
    "撮合",
    "交割",
    "監理",
    "法規",
    "裁罰",
    "複委託",
    "跨境",
    "券商",
    "證券商",
    "online broker",
    "retail brokerage",
    "brokerage platform",
    "trading app",
    "zero commission",
    "commission-free",
    "market structure",
    "regulation",
    "regulatory",
    "investor protection",
    "tokenization",
    "tokenized securities",
    "digital securities",
] + BROKERAGE_NAMES

HIGH_IMPACT_ACTIONS = [
    "通過",
    "核准",
    "正式上路",
    "修法",
    "裁罰",
    "禁止",
    "收購",
    "合併",
    "退出市場",
    "adopts",
    "approves",
    "mandates",
    "enforcement",
    "acquisition",
]

MEDIUM_IMPACT_ACTIONS = [
    "提案",
    "公開諮詢",
    "宣布",
    "推出",
    "擴張",
    "合作",
    "投資",
    "proposes",
    "consults",
    "announces",
    "launches",
    "expands",
    "partners",
    "invests",
]

LOW_IMPACT_ACTIONS = [
    "研議",
    "考慮",
    "預計",
    "傳出",
    "may",
    "considers",
    "reportedly",
]

OFFICIAL_SOURCES = [
    "金管會",
    "證交所",
    "櫃買",
    "SEC",
    "FINRA",
    "ESMA",
    "DTCC",
    "香港證監會",
    "日本金融廳",
    "韓國金融監理院",
]

BROKER_OFFICIAL_SOURCES = [
    "Robinhood",
    "Charles Schwab",
    "Futu",
    "SBI",
    "Mirae Asset",
    "Samsung Securities",
    "Rakuten Securities",
]

MAINSTREAM_MEDIA_SOURCES = [
    "工商時報",
    "經濟日報",
    "MoneyDJ",
    "鉅亨",
    "日經",
    "Reuters",
    "Yahoo Finance",
    "Bloomberg",
]

LOW_QUALITY_SOURCES = [
    "AD HOC NEWS",
    "finance.biggo",
    "TronWeekly",
]

EXCLUDED_SOURCES = [
    "CMoney",
]

SOURCE_PENALTIES = {
    "moomoo": 4,
    "Yahoo Finance": 2,
}

CRITICAL_COMMENTARY_KEYWORDS = [
    "批評",
    "批判",
    "抨擊",
    "砲轟",
    "炮轟",
    "怒轟",
    "遭批",
    "被批",
    "遭酸",
    "被酸",
    "罵翻",
    "炎上",
    "爭議",
    "質疑",
    "不滿",
    "抱怨",
    "網友",
    "輿論",
    "criticism",
    "criticized",
    "criticised",
    "criticizes",
    "criticises",
    "slammed",
    "blasted",
    "backlash",
    "under fire",
    "controversy",
    "controversial",
    "complaint",
    "complaints",
    "disappointed",
    "angry",
    "outrage",
    "boycott",
]

CRITICAL_EXCEPTION_KEYWORDS = [
    "裁罰",
    "罰款",
    "處分",
    "起訴",
    "控告",
    "調查",
    "禁止",
    "和解",
    "修法",
    "通過",
    "核准",
    "正式上路",
    "enforcement",
    "fine",
    "fined",
    "penalty",
    "penalties",
    "charges",
    "charged",
    "settlement",
    "lawsuit",
    "probe",
    "investigation",
    "ban",
    "banned",
    "adopts",
    "approves",
    "mandates",
]

INVESTOR_CONTENT_KEYWORDS = [
    "投資教學",
    "商品介紹",
    "投資人觀點",
    "投資人看法",
    "投資人情緒",
    "投資組合",
    "股息",
    "配息",
    "殖利率",
    "存股",
    "推薦股票",
    "個股推薦",
    "how to buy",
    "should you buy",
    "top stocks",
    "stock picks",
    "price prediction",
    "portfolio",
    "dividend",
    "technical analysis",
    "investor sentiment",
    "watchlist",
]

EDUCATIONAL_CONTENT_KEYWORDS = [
    "教育",
    "教學",
    "入門",
    "指南",
    "懶人包",
    "新手",
    "學會",
    "課程",
    "講座",
    "研討會",
    "webinar",
    "learn",
    "learning",
    "guide",
    "explainer",
    "beginner",
    "beginners",
    "tutorial",
    "education",
    "educational",
    "course",
    "seminar",
]

PROFILE_CONTENT_KEYWORDS = [
    "人物",
    "人物專訪",
    "專訪",
    "人物介紹",
    "創辦人故事",
    "職涯",
    "履歷",
    "任命",
    "接任",
    "升任",
    "卸任",
    "辭任",
    "辭職",
    "離職",
    "董事長",
    "總經理",
    "執行長",
    "profile",
    "interview",
    "q&a",
    "career",
    "biography",
    "bio",
    "founder story",
    "meet the",
    "CEO",
    "CFO",
    "president",
    "chairman",
    "chief executive",
    "appointed",
    "appoints",
    "names",
    "steps down",
    "resigns",
    "succession",
]

TECH_VENDOR_SIGNAL_KEYWORDS = [
    "AI",
    "artificial intelligence",
    "crypto",
    "cryptocurrency",
    "web3",
    "RWA",
    "fintech",
    "tokenization",
    "tokenized",
    "platform",
    "funding",
    "raises",
    "launch",
    "launches",
    "startup",
    "solution provider",
    "technology provider",
]

BROKERAGE_CORE_TERMS = [
    "券商",
    "證券商",
    "複委託",
    "brokerage",
    "broker-dealer",
    "online broker",
    "retail broker",
    "retail brokerage",
    "digital brokerage",
    "broker app",
    "trading app",
    "zero commission",
    "commission-free",
]

MARKET_RULE_CORE_TERMS = [
    "金管會",
    "證交所",
    "櫃買",
    "交易制度",
    "延長交易",
    "逐筆交易",
    "零股",
    "撮合",
    "交割",
    "監理",
    "法規",
    "裁罰",
    "market structure",
    "market design",
    "securities regulation",
    "investor protection",
    "clearing",
    "settlement",
    "central counterparty",
    "post trade",
    "T+1",
    "T+2",
]

REGULATOR_TITLE_TERMS = [
    "金管會",
    "證交所",
    "櫃買",
    "SEC",
    "FINRA",
    "ESMA",
    "DTCC",
    "香港證監會",
    "日本金融廳",
    "韓國金融監理院",
]

SECURITIES_MARKET_TITLE_TERMS = [
    "證券",
    "證券商",
    "券商",
    "資本市場",
    "securities",
    "capital market",
    "broker",
    "brokerage",
    "broker-dealer",
    "trading",
    "clearing",
    "settlement",
    "market structure",
    "market design",
]

PRELIMINARY_SCORE_THRESHOLD = 8


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
            if title_key in seen_titles or _is_near_duplicate(title_tokens, seen_title_tokens):
                continue

            published_at = _entry_datetime(entry)
            if published_at and published_at < cutoff:
                continue

            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            clean_summary = _clean_summary(summary)
            if not _is_relevant(title, clean_summary, source.name, published_at):
                continue

            score = _importance_score(title, clean_summary, source.name, published_at)
            article = Article(
                title=title,
                url=url,
                source=source.name,
                published_at=published_at,
                summary=clean_summary,
            )

            if event_key and event_key in seen_event_keys:
                for index, (existing_score, existing_article) in enumerate(scored_articles):
                    if _event_key(existing_article.title) == event_key:
                        existing_time = existing_article.published_at or datetime.min.replace(tzinfo=UTC)
                        new_time = published_at or datetime.min.replace(tzinfo=UTC)
                        if score > existing_score or (score == existing_score and new_time > existing_time):
                            scored_articles[index] = (score, article)
                        break
                continue

            seen_urls.add(url)
            seen_titles.add(title_key)
            if event_key:
                seen_event_keys.add(event_key)
            seen_title_tokens.append(title_tokens)
            scored_articles.append((score, article))

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


def _is_relevant(title: str, summary: str, source: str, published_at: datetime | None) -> bool:
    lower_title = title.lower()
    lower_text = f"{title}\n{summary}".lower()

    strategic_hits = _count_hits(lower_text, STRATEGIC_KEYWORDS)
    broker_hits = _count_hits(lower_text, BROKERAGE_NAMES)
    macro_hits = _count_hits(lower_text, MACRO_CONTEXT_KEYWORDS)
    business_hits = _count_hits(lower_text, BROKERAGE_BUSINESS_KEYWORDS)
    hard_noise_hit = any(keyword.lower() in lower_text for keyword in HARD_NOISE_KEYWORDS)
    hard_exclude_hit = any(keyword.lower() in lower_text for keyword in HARD_EXCLUDE_KEYWORDS) or any(
        pattern.search(f"{title}\n{summary}") for pattern in HARD_EXCLUDE_PATTERNS
    )
    preliminary_score = _importance_score(title, summary, source, published_at, include_soft_penalty=False)

    if _is_excluded_source(source):
        return False

    if hard_noise_hit:
        return False

    if _is_investor_or_product_content(lower_text):
        return False

    if _is_education_or_profile_content(lower_text):
        return False

    if _is_non_focus_tech_vendor_article(lower_title, lower_text, source):
        return False

    if not _has_required_focus(lower_title, lower_text, source):
        return False

    if _is_non_focus_wealth_management(lower_text):
        return False

    if _is_pure_marketing(lower_text):
        return False

    if _is_critical_commentary(lower_text):
        return False

    if hard_exclude_hit and not _has_strong_exception(lower_text):
        return False

    if broker_hits and business_hits:
        return True

    if business_hits and macro_hits:
        return True

    if strategic_hits >= 2 and (macro_hits >= 1 or business_hits >= 1):
        return True

    return preliminary_score >= PRELIMINARY_SCORE_THRESHOLD


def _is_excluded_source(source: str) -> bool:
    lower_source = source.lower()
    return any(keyword.lower() in lower_source for keyword in EXCLUDED_SOURCES)


def _is_critical_commentary(lower_text: str) -> bool:
    critical_hit = any(_contains_keyword(lower_text, keyword) for keyword in CRITICAL_COMMENTARY_KEYWORDS)
    if not critical_hit:
        return False

    return not any(_contains_keyword(lower_text, keyword) for keyword in CRITICAL_EXCEPTION_KEYWORDS)


def _is_investor_or_product_content(lower_text: str) -> bool:
    content_hit = any(_contains_keyword(lower_text, keyword) for keyword in INVESTOR_CONTENT_KEYWORDS)
    if not content_hit:
        return False

    return not any(_contains_keyword(lower_text, keyword) for keyword in CRITICAL_EXCEPTION_KEYWORDS)


def _is_education_or_profile_content(lower_text: str) -> bool:
    education_hit = any(_contains_keyword(lower_text, keyword) for keyword in EDUCATIONAL_CONTENT_KEYWORDS)
    profile_hit = any(_contains_keyword(lower_text, keyword) for keyword in PROFILE_CONTENT_KEYWORDS)
    return education_hit or profile_hit


def _is_non_focus_tech_vendor_article(lower_title: str, lower_text: str, source: str) -> bool:
    tech_hit = any(_contains_keyword(lower_text, keyword) for keyword in TECH_VENDOR_SIGNAL_KEYWORDS)
    if not tech_hit:
        return False

    return not _has_required_focus(lower_title, lower_text, source)


def _has_required_focus(lower_title: str, lower_text: str, source: str) -> bool:
    if any(_contains_keyword(lower_title, keyword) for keyword in BROKERAGE_NAMES):
        return True

    if any(_contains_keyword(lower_title, keyword) for keyword in BROKERAGE_CORE_TERMS):
        return True

    if any(_contains_keyword(lower_title, keyword) for keyword in MARKET_RULE_CORE_TERMS):
        return True

    lower_source = source.lower()
    official_source = any(keyword.lower() in lower_source for keyword in OFFICIAL_SOURCES)
    if official_source and any(_contains_keyword(lower_title, keyword) for keyword in SECURITIES_MARKET_TITLE_TERMS):
        return True

    regulator_in_title = any(_contains_keyword(lower_title, keyword) for keyword in REGULATOR_TITLE_TERMS)
    securities_market_context = any(_contains_keyword(lower_title, keyword) for keyword in SECURITIES_MARKET_TITLE_TERMS)
    if regulator_in_title and securities_market_context:
        return True

    title_is_ambiguous_broker_news = any(_contains_keyword(lower_title, keyword) for keyword in ["launch", "launches", "expand", "expands", "partners", "acquisition"])
    summary_has_broker_context = any(_contains_keyword(lower_text, keyword) for keyword in BROKERAGE_NAMES + BROKERAGE_CORE_TERMS)
    if title_is_ambiguous_broker_news and summary_has_broker_context:
        return True

    return False


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


def _importance_score(
    title: str,
    summary: str,
    source: str,
    published_at: datetime | None,
    *,
    include_soft_penalty: bool = True,
) -> float:
    score = 0.0

    for _, cap, keywords in TOPIC_GROUPS:
        score += _capped_topic_score(title, summary, keywords, cap)

    score += _action_score(title, summary)
    score += _source_authority_score(source)
    score += _recency_score(published_at)

    lower_text = f"{title}\n{summary}".lower()
    if any(name.lower() in lower_text for name in BROKERAGE_NAMES) and any(
        keyword in lower_text for keyword in ["布局", "佈局", "strategy", "strategic", "launch", "expand", "launches"]
    ):
        score += 4

    if include_soft_penalty:
        score -= _source_penalty(source)
        score -= _soft_noise_penalty(title, summary)
        score -= _marketing_penalty(title, summary)
        score -= _wealth_management_penalty(title, summary)

    return score


def _count_hits(lower_text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword.lower() in lower_text)


def _contains_keyword(lower_text: str, keyword: str) -> bool:
    lower_keyword = keyword.lower()
    if re.fullmatch(r"[a-z0-9 -]+", lower_keyword):
        pattern = rf"(?<![a-z0-9]){re.escape(lower_keyword)}(?![a-z0-9])"
        return re.search(pattern, lower_text) is not None
    return lower_keyword in lower_text


def _weighted_keyword_hits(title: str, summary: str, keywords: list[str]) -> float:
    title_text = title.lower()
    summary_text = summary.lower()
    score = 0.0
    for keyword in keywords:
        lower_keyword = keyword.lower()
        if lower_keyword in title_text:
            score += 1.0
        elif lower_keyword in summary_text:
            score += 0.4
    return score


def _capped_topic_score(title: str, summary: str, keywords: list[str], cap: int) -> float:
    return min(cap, _weighted_keyword_hits(title, summary, keywords) * 2)


def _action_score(title: str, summary: str) -> int:
    text = f"{title}\n{summary}".lower()
    if any(keyword.lower() in text for keyword in HIGH_IMPACT_ACTIONS):
        return 8
    if any(keyword.lower() in text for keyword in MEDIUM_IMPACT_ACTIONS):
        return 5
    if any(keyword.lower() in text for keyword in LOW_IMPACT_ACTIONS):
        return 1
    return 0


def _source_authority_score(source: str) -> int:
    lower_source = source.lower()
    if any(keyword.lower() in lower_source for keyword in OFFICIAL_SOURCES):
        return 6
    if any(keyword.lower() in lower_source for keyword in BROKER_OFFICIAL_SOURCES):
        return 4
    if any(keyword.lower() in lower_source for keyword in MAINSTREAM_MEDIA_SOURCES):
        return 2
    if any(keyword.lower() in lower_source for keyword in LOW_QUALITY_SOURCES):
        return -3
    return 0


def _source_penalty(source: str) -> int:
    lower_source = source.lower()
    return sum(points for keyword, points in SOURCE_PENALTIES.items() if keyword.lower() in lower_source)


def _recency_score(published_at: datetime | None) -> int:
    if published_at is None:
        return -2

    age = datetime.now(UTC) - published_at
    if age <= timedelta(hours=12):
        return 2
    if age <= timedelta(hours=24):
        return 1
    return 0


def _soft_noise_penalty(title: str, summary: str) -> int:
    text = f"{title}\n{summary}".lower()
    penalty = 0
    for keywords, points in SOFT_NOISE_GROUPS:
        if any(keyword.lower() in text for keyword in keywords):
            penalty += points
    return min(penalty, 8)


def _wealth_management_penalty(title: str, summary: str) -> int:
    text = f"{title}\n{summary}".lower()
    if any(_contains_keyword(text, keyword) for keyword in WEALTH_MANAGEMENT_KEYWORDS):
        return 6
    return 0


def _is_non_focus_wealth_management(lower_text: str) -> bool:
    wealth_hit = any(_contains_keyword(lower_text, keyword) for keyword in WEALTH_MANAGEMENT_KEYWORDS)
    if not wealth_hit:
        return False

    return not any(_contains_keyword(lower_text, keyword) for keyword in CORE_FOCUS_KEYWORDS)


def _marketing_penalty(title: str, summary: str) -> int:
    text = f"{title}\n{summary}".lower()
    if not any(keyword.lower() in text for keyword in PURE_MARKETING_KEYWORDS):
        return 0
    return 10
