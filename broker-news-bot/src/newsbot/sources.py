from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class NewsSource:
    name: str
    url: str


def google_news_source(name: str, query: str, *, lang: str = "zh-TW", region: str = "TW") -> NewsSource:
    encoded_query = quote_plus(f"({query}) when:1d")
    ceid_lang = "zh-Hant" if lang == "zh-TW" else lang.split("-", maxsplit=1)[0]
    return NewsSource(
        name=name,
        url=f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={region}&ceid={region}:{ceid_lang}",
    )


RSS_SOURCES: list[NewsSource] = [
    NewsSource("金管會新聞稿", "https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2&mcustomize=news_rss.jsp"),
    NewsSource("證交所新聞", "https://www.twse.com.tw/rss/news.xml"),
    NewsSource("櫃買中心新聞", "https://www.tpex.org.tw/web/about/news/news/rss.php"),
    google_news_source("工商時報", "site:ctee.com.tw 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託 OR 財富管理"),
    google_news_source("經濟日報", "site:money.udn.com 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託 OR 財富管理"),
    google_news_source("MoneyDJ", "site:moneydj.com 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託 OR 財富管理"),
    google_news_source("鉅亨網", "site:cnyes.com 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託 OR 財富管理"),
    google_news_source("CMoney", "site:cmoney.tw 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託 OR 財富管理"),
    google_news_source("moomoo", "site:moomoo.com brokerage OR broker strategy OR wealth management OR retail investor platform", lang="en-US", region="US"),
    google_news_source("日經", "site:nikkei.com OR site:asia.nikkei.com brokerage strategy OR securities industry OR retail brokerage OR wealth management", lang="en-US", region="US"),
    google_news_source("韓國金融監理院", "site:fss.or.kr securities company OR capital market OR brokerage OR investor protection", lang="en-US", region="KR"),
    google_news_source("日本金融廳", "site:fsa.go.jp securities company OR brokerage OR financial instruments business OR investor protection", lang="en-US", region="JP"),
    google_news_source("香港證監會", "site:sfc.hk broker OR brokerage OR securities regulation OR virtual asset trading platform", lang="en-US", region="HK"),
    google_news_source("Reuters", "site:reuters.com Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Samsung Securities OR Rakuten Securities", lang="en-US", region="US"),
    google_news_source("Yahoo Finance", "site:finance.yahoo.com Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Samsung Securities OR Rakuten Securities", lang="en-US", region="US"),
    google_news_source("Bloomberg", "site:bloomberg.com Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Samsung Securities OR Rakuten Securities", lang="en-US", region="US"),
    google_news_source("台灣券商綜合", "券商 交易制度 OR 券商 財富管理 OR 券商 複委託 OR 證券商 戰略 OR 金管會 券商"),
    google_news_source("海外券商戰略", "Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Mirai Asset OR Samsung Securities OR Rakuten Securities OR Rakutan Securities", lang="en-US", region="US"),
    google_news_source("海外網路券商趨勢", "online broker strategy OR retail brokerage trend OR broker app OR brokerage platform OR zero commission", lang="en-US", region="US"),
    NewsSource("SEC Press Releases", "https://www.sec.gov/news/pressreleases.rss"),
    NewsSource("FINRA News", "https://www.finra.org/rss/news-releases.xml"),
]
