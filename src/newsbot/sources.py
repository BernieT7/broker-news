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
    google_news_source("工商時報", "site:ctee.com.tw 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託"),
    google_news_source("經濟日報", "site:money.udn.com 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託"),
    google_news_source("鉅亨網", "site:cnyes.com 券商 OR 證券商 OR 金管會 OR 交易制度 OR 零股 OR 複委託"),
    google_news_source("日經", "site:nikkei.com OR site:asia.nikkei.com brokerage strategy OR securities industry OR retail brokerage", lang="en-US", region="US"),
    google_news_source("韓國金融監理院", "site:fss.or.kr securities company OR capital market OR brokerage OR investor protection", lang="en-US", region="KR"),
    google_news_source("日本金融廳", "site:fsa.go.jp securities company OR brokerage OR financial instruments business OR investor protection", lang="en-US", region="JP"),
    google_news_source("香港證監會", "site:sfc.hk broker OR brokerage OR securities regulation OR virtual asset trading platform", lang="en-US", region="HK"),
    google_news_source("Reuters", "site:reuters.com Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Samsung Securities OR Rakuten Securities", lang="en-US", region="US"),
    google_news_source("Yahoo Finance", "site:finance.yahoo.com Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Samsung Securities OR Rakuten Securities", lang="en-US", region="US"),
    google_news_source("Bloomberg", "site:bloomberg.com Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Samsung Securities OR Rakuten Securities", lang="en-US", region="US"),
    google_news_source("台灣券商綜合", "券商 交易制度 OR 券商 複委託 OR 證券商 戰略 OR 金管會 券商"),
    google_news_source("海外券商戰略", "Robinhood OR Charles Schwab OR Futu OR SBI Securities OR Mirae Asset OR Mirai Asset OR Samsung Securities OR Rakuten Securities OR Rakutan Securities", lang="en-US", region="US"),
    google_news_source("海外網路券商趨勢", "online broker strategy OR retail brokerage trend OR broker app OR brokerage platform OR zero commission", lang="en-US", region="US"),
    google_news_source("美國零售券商", "Fidelity brokerage OR E*TRADE OR E-Trade OR Webull OR SoFi Invest retail brokerage", lang="en-US", region="US"),
    google_news_source("歐洲零售券商", "eToro OR DEGIRO OR Trading 212 OR IG Group OR XTB OR Trade Republic OR Scalable Capital OR Saxo Bank retail brokerage", lang="en-US", region="GB"),
    google_news_source("加拿大零售券商", "Wealthsimple OR Questrade retail brokerage OR online broker", lang="en-US", region="CA"),
    google_news_source("印度零售券商", "Zerodha OR Groww OR Upstox OR Angel One retail brokerage OR stock broker", lang="en-US", region="IN"),
    google_news_source("亞太零售券商", "Tiger Brokers OR Monex OR Kiwoom Securities OR CommSec OR Stake retail brokerage OR online broker", lang="en-US", region="SG"),
    google_news_source(
        "全球監管機構",
        "IOSCO OR CFTC OR NFA OR FCA OR CIRO OR OSC OR ASIC OR MAS OR SEBI OR CSRC securities regulation brokerage market structure",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "歐洲中東非監管",
        "BaFin OR AMF France OR FINMA OR DFSA Dubai OR FSRA Abu Dhabi OR Saudi CMA OR FSCA securities regulation broker",
        lang="en-US",
        region="GB",
    ),
    google_news_source(
        "拉丁美洲監管",
        "Brazil CVM OR Mexico CNBV securities regulation brokerage capital markets",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "新興金融商品策略",
        "RWA OR STO OR tokenization OR tokenized securities OR security token OR digital securities OR on-chain settlement OR on-chain clearing "
        "BlackRock OR JPMorgan OR Goldman Sachs OR bank OR exchange OR regulator OR broker OR task force",
        lang="en-US",
        region="US",
    ),
    NewsSource("DTCC 官方公告", "https://www.dtcc.com/news"),
    google_news_source(
        "新興金融商品策略中文",
        "RWA OR STO OR 代幣化 OR 數位證券 OR 代幣化證券 OR 證券型代幣 OR 鏈上結算 OR 鏈上交割 "
        "貝萊德 OR 摩根大通 OR 高盛 OR 銀行 OR 交易所 OR 監管 OR 券商 OR 小組",
    ),
    google_news_source(
        "機構代幣化可靠來源",
        "site:ledgerinsights.com OR site:coindesk.com OR site:theblock.co OR site:dlnews.com OR site:blockworks.co "
        "RWA OR tokenized securities OR digital securities OR security token OR on-chain settlement",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "全球財經媒體",
        "site:ft.com OR site:wsj.com OR site:reuters.com OR site:bloomberg.com brokerage OR securities regulation OR tokenized securities OR market structure",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "亞洲財經媒體",
        "site:asia.nikkei.com OR site:scmp.com OR site:businesstimes.com.sg OR site:caixin.com OR site:economictimes.indiatimes.com OR site:afr.com brokerage OR securities regulation OR online broker",
        lang="en-US",
        region="SG",
    ),
    google_news_source(
        "歐洲財經媒體",
        "site:fnlondon.com OR site:handelsblatt.com OR site:lesechos.fr OR site:ilsole24ore.com brokerage OR securities regulation OR retail broker",
        lang="en-US",
        region="GB",
    ),
    google_news_source(
        "券商金融科技專業媒體",
        "site:financemagnates.com OR site:fintechfutures.com OR site:globalfintechseries.com OR site:thefintechtimes.com "
        "brokerage OR broker OR trading platform OR clearing OR settlement",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "市場基礎設施專業媒體",
        "site:tradersmagazine.com OR site:marketsmedia.com OR site:waterstechnology.com "
        "broker OR exchange OR clearing OR settlement OR market structure OR order routing",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "數位證券專業媒體",
        "site:ledgerinsights.com OR site:coindesk.com OR site:theblock.co OR site:blockworks.co OR site:dlnews.com "
        "tokenized securities OR tokenized stocks OR on-chain settlement OR broker-dealer OR custody",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "企業新聞稿",
        "site:businesswire.com OR site:prnewswire.com OR site:globenewswire.com OR site:stocktitan.net "
        "brokerage OR broker-dealer OR exchange OR clearing OR settlement OR trading platform",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "網路券商官方新聞",
        "site:robinhood.com/newsroom OR site:interactivebrokers.com OR site:sofi.com/press OR site:webull.com/news "
        "OR site:etoro.com/news-and-analysis OR site:traderepublic.com OR site:wealthsimple.com OR site:alpaca.markets/blog "
        "launch OR partnership OR expansion OR clearing OR settlement OR custody OR trading",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "亞太網路券商官方新聞",
        "site:futuholdings.com OR site:sbisec.co.jp OR site:rakuten-sec.co.jp OR site:monexgroup.jp "
        "launch OR partnership OR market OR trading OR settlement",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "市場基礎設施官方新聞",
        "site:nyse.com OR site:nasdaq.com OR site:memx.com OR site:cboe.com OR site:cmegroup.com OR site:lseg.com "
        "OR site:dtcc.com OR site:euroclear.com OR site:clearstream.com OR site:hkexgroup.com OR site:sgx.com "
        "OR site:jpx.co.jp OR site:global.krx.co.kr clearing OR settlement OR market structure OR trading hours OR tokenized securities",
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "券商產品與基礎設施搜尋",
        '"online broker launch" OR "retail brokerage platform" OR "brokerage infrastructure" OR '
        '"brokerage-as-a-service" OR "Alpaca brokerage infrastructure" OR "broker API trading"',
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "券商AI與交易技術搜尋",
        '"AI trading broker" OR "Model Context Protocol brokerage" OR "order routing broker" OR '
        '"extended-hours trading broker" OR "24-hour trading equities broker"',
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "證券代幣化與事件合約搜尋",
        '"securities settlement tokenized" OR "tokenized securities settlement" OR '
        '"on-chain settlement securities" OR "exchange prediction contracts" OR "event contracts broker"',
        lang="en-US",
        region="US",
    ),
    google_news_source(
        "券商收益模式搜尋",
        '"broker cash sweep" OR "securities lending broker" OR "margin lending broker" OR '
        '"Interactive Brokers exchange" OR "Robinhood trading"',
        lang="en-US",
        region="US",
    ),
    NewsSource("SEC Press Releases", "https://www.sec.gov/news/pressreleases.rss"),
    NewsSource("FINRA News", "https://www.finra.org/rss/news-releases.xml"),
]
