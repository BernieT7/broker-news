from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen
from types import SimpleNamespace

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
    "CFTC",
    "NFA",
    "FCA",
    "CIRO",
    "OSC",
    "ASIC",
    "MAS",
    "SEBI",
    "CSRC",
    "BaFin",
    "AMF",
    "FINMA",
    "IOSCO",
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
    "Fidelity",
    "Fidelity Investments",
    "E*TRADE",
    "E-Trade",
    "ETRADE",
    "Webull",
    "SoFi Invest",
    "SoFi",
    "eToro",
    "DEGIRO",
    "Trading 212",
    "IG Group",
    "XTB",
    "Wealthsimple",
    "Questrade",
    "Zerodha",
    "Groww",
    "Upstox",
    "Angel One",
    "CommSec",
    "Stake",
    "Tiger Brokers",
    "Monex",
    "Kiwoom Securities",
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
    "券商評等",
    "券商評價",
    "券商給予",
    "券商看好",
    "券商建議",
    "排行",
    "前20名",
    "IPO價格",
    "IPO 價格",
    "IPO定價",
    "IPO 定價",
    "招股價",
    "發行價",
    "上市價",
    "承銷價",
    "灰市",
    "灰市價",
    "灰市價格",
    "灰市溢價",
    "暗盤",
    "暗盤價",
    "暗盤價格",
    "申購建議",
    "抽籤建議",
    "認購建議",
    "申購攻略",
    "值得申購",
    "可以申購",
    "要不要申購",
    "抽不抽",
    "中籤率",
    "申購價",
    "股市爆料同學會",
    "撿零股",
    "違約交割慘案",
    "被動元件股王",
    "通報翻車",
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
    "槓桿ETF",
    "槓桿 ETF",
    "散戶損手",
    "最低保證金",
    "cfd brokerage platform",
    "multi-asset cfd brokerage platform",
    "base markets announces",
    "hidden costs of disconnected brokerage systems",
    "disconnected brokerage systems",
    "real estate",
    "比特幣",
    "bitcoin",
    "Bitcoin",
    "BTC",
    "btc",
    "bitcoin ETF",
    "spot bitcoin",
    "現貨比特幣",
    "比特幣ETF",
    "比特幣 ETF",
    "內線交易",
    "內線交易監控",
    "內線交易查核",
    "內線交易防制",
    "內線交易案",
    "內線交易調查",
    "內部人交易",
    "市場濫用監控",
    "市場濫用",
    "市場操縱監控",
    "市場操縱",
    "操縱市場",
    "異常交易監控",
    "異常交易查核",
    "可疑交易",
    "insider trading",
    "insider dealing",
    "insider transaction",
    "market abuse",
    "market abuse surveillance",
    "market abuse monitoring",
    "market manipulation",
    "trade surveillance",
    "trading surveillance",
    "surveillance alert",
    "suspicious trading",
    "rumor",
    "spreading rumors",
    "個股",
    "焦點股",
    "台指期",
    "期貨速報",
    "technical analysis",
    "price target",
    "target price",
    "ipo price",
    "ipo pricing",
    "issue price",
    "offer price",
    "listing price",
    "grey market",
    "gray market",
    "grey market premium",
    "gray market premium",
    "gmp",
    "subscription advice",
    "ipo subscription",
    "subscribe or avoid",
    "should you subscribe",
    "broker rating",
    "broker recommendation",
    "brokerage rating",
    "brokerage recommendation",
    "which brokerage stock",
    "better buy",
    "class action",
    "securities fraud",
    "stock decline",
    "undisclosed regulatory compliance",
    "investors may contact",
    "law firm",
    "shareholder alert",
    "shareholder notice",
    "lead plaintiff",
    "losses in excess",
    "Kahn Swick",
    "Foti",
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
    "基金理財網",
    "基金理財",
    "投資闖關賽",
    "闖關賽",
    "投資新常態",
    "土地銀行基金理財網",
    "裁罰案彙整名單",
    "公開發行公司等動態",
    "股票禮品卡",
    "全民送股",
    "裁罰近億元",
    "裁罰9787萬元",
    "裁罰9,787萬元",
    "上半年裁罰",
    "H1裁罰",
    "h1裁罰",
    "銀行業連吞",
    "銀行業吞",
    "大罰單",
    "大開鍘",
    "達成率",
    "裁罰風向",
    "爆料",
]

ABSOLUTE_EXCLUDE_KEYWORDS = [
    "class action",
    "securities fraud",
    "stock decline",
    "undisclosed regulatory compliance",
    "investors may contact",
    "law firm",
    "shareholder alert",
    "shareholder notice",
    "lead plaintiff",
    "losses in excess",
    "Kahn Swick",
    "Foti",
    "KuCoin",
    "裁罰案彙整名單",
    "公開發行公司等動態",
    "股票禮品卡",
    "全民送股",
    "槓桿ETF",
    "槓桿 ETF",
    "散戶損手",
    "cfd brokerage platform",
    "multi-asset cfd brokerage platform",
    "base markets announces",
    "hidden costs of disconnected brokerage systems",
    "disconnected brokerage systems",
    "裁罰瞄準重大案件",
    "裁罰近億元",
    "裁罰9787萬元",
    "裁罰9,787萬元",
    "上半年裁罰",
    "H1裁罰",
    "h1裁罰",
    "銀行業連吞",
    "銀行業吞",
    "大罰單",
    "大開鍘",
    "裁罰風向",
    "小案少、大案重",
]

ABSOLUTE_EXCLUDE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"金管會.*裁罰.*(億元|萬元|大單|大罰單|達成率|風向|重大案件|小案少|大案重)",
        r"證期局.*裁罰案彙整",
        r"裁罰案彙整.*公開發行公司",
        r"股票禮品卡",
        r"announces full launch.*cfd brokerage platform",
        r"hidden costs of disconnected brokerage systems",
        r"ETF.*散戶.*(損|震盪)",
        r"槓桿\s*ETF.*(散戶|保證金|入場門檻)",
        r"券商.*最低保證金.*ETF",
        r"裁罰.*(銀行業|銀行局).*(大單|大罰單|開鍘|達成率)",
        r"上半年.*裁罰.*(億元|萬元)",
        r"h1.*裁罰.*(億元|萬元)",
    ]
]

ALERT_LIST_URL_KEYWORDS = [
    "/alert-list/",
    "investor-alert",
    "investor alert",
    "warning-list",
    "warning list",
    "unlicensed-entities",
    "unlicensed entities",
    "suspicious-websites",
    "suspicious websites",
    "unauthorised-firms",
    "unauthorised firms",
    "unauthorized-firms",
    "unauthorized firms",
]

INDIVIDUAL_ALERT_KEYWORDS = [
    "未獲發牌",
    "無牌經營",
    "未經授權",
    "可疑網站",
    "冒牌公司",
    "投資者警示",
    "投資人警示",
    "警示名單",
    "unlicensed entity",
    "unlicensed entities",
    "unauthorised firm",
    "unauthorised firms",
    "unauthorized firm",
    "unauthorized firms",
    "suspicious website",
    "suspicious websites",
    "clone firm",
    "clone firms",
    "investor alert",
    "warning list",
    "not licensed",
    "not authorised",
    "not authorized",
]

ALERT_STRATEGY_EXCEPTION_KEYWORDS = [
    "新規則",
    "新規",
    "政策",
    "修法",
    "法規",
    "監理標準",
    "監管標準",
    "執法政策",
    "執法行動",
    "跨國執法",
    "大規模",
    "多家",
    "一批",
    "一次查處",
    "持牌",
    "廣告",
    "招攬客戶",
    "投資人保護規則",
    "投資者保護規則",
    "產業",
    "趨勢",
    "統計",
    "年增",
    "倍增",
    "冒名",
    "深偽",
    "社群投資詐騙",
    "new rule",
    "new rules",
    "policy",
    "regulatory standard",
    "regulatory standards",
    "enforcement policy",
    "enforcement action",
    "cross-border enforcement",
    "crackdown",
    "sweep",
    "multiple",
    "dozens",
    "licensing",
    "advertising",
    "solicitation",
    "investor protection rule",
    "industry",
    "trend",
    "statistics",
    "data shows",
    "year-on-year",
    "clone scams",
    "deepfake",
    "social media investment scams",
]

INDIVIDUAL_CORPORATE_FILING_KEYWORDS = [
    "registration statement",
    "registration statement (equity securities)",
    "correction of statement",
    "correction of registration statement",
    "equity securities",
    "ipo prospectus",
    "prospectus",
    "offering results",
    "offering result",
    "individual company listing",
    "listing filing",
    "corporate filings",
    "repository of korea's corporate filings",
    "dart",
    "증권신고서",
    "정정신고서",
    "코스닥 상장",
    "申報書",
    "證券申報書",
    "更正申報書",
    "修正版申報書",
    "上市申報",
]

CORPORATE_FILING_STRATEGY_EXCEPTION_KEYWORDS = [
    "ipo制度",
    "ipo 制度",
    "承銷規則",
    "承銷制度",
    "配售制度",
    "零售配售",
    "市場改革",
    "上市制度",
    "上市規則",
    "多家ipo",
    "多家 IPO",
    "集中撤件",
    "定價失敗",
    "監管要求補件",
    "ipo rule",
    "ipo rules",
    "underwriting rule",
    "underwriting rules",
    "allocation rule",
    "retail allocation",
    "listing reform",
    "listing rules",
    "market reform",
    "pricing failures",
    "withdrawn ipos",
    "withdrawal wave",
]

BROKER_EARNINGS_NOISE_KEYWORDS = [
    "earnings",
    "quarterly results",
    "quarterly earnings",
    "profit",
    "profits",
    "revenue",
    "stock",
    "stocks",
    "shares",
    "bull market",
    "bear market",
    "how that will impact earnings",
    "trading at a discount",
    "at a discount",
    "財報",
    "獲利",
    "營收",
    "股價",
    "股票",
]

BROKER_EARNINGS_STRATEGY_EXCEPTION_KEYWORDS = [
    "launch",
    "launches",
    "expand",
    "expands",
    "partnership",
    "partners",
    "platform",
    "regulation",
    "regulatory",
    "market structure",
    "settlement",
    "clearing",
    "tokenization",
    "tokenized securities",
    "RWA",
    "STO",
    "推出",
    "上線",
    "擴張",
    "合作",
    "平台",
    "監管",
    "法規",
    "交易制度",
    "交割",
    "清算",
    "代幣化",
    "證券型代幣",
]

BROKER_COMMENTARY_MARKERS = [
    "券商：",
    "券商:",
    "券商表示",
    "券商指出",
    "券商認為",
    "券商看好",
    "券商研報",
    "broker says",
    "brokerage says",
    "brokerage sees",
    "analysts at",
]

NON_BROKER_INDUSTRY_COMMENTARY_KEYWORDS = [
    "AI",
    "ai",
    "半導體",
    "記憶體",
    "晶片",
    "科技股",
    "主權AI",
    "中東主權AI",
    "memory",
    "semiconductor",
    "chip",
    "chips",
    "commodity",
    "commodities",
    "原物料",
    "韓股",
    "景氣",
    "市場焦點",
    "memory chip",
]

INDIVIDUAL_TRADING_STATUS_KEYWORDS = [
    "公告本公司",
    "恢復買賣",
    "停止買賣",
    "暫停買賣",
    "終止買賣",
    "終止興櫃",
    "終止興櫃買賣",
    "興櫃買賣",
    "恢復在證券商營業處所買賣",
    "證券商營業處所買賣",
    "恢復為普通交割",
    "普通交割",
    "變更交易方法",
    "恢復融資融券",
    "融資融券交易",
]

TRADING_STATUS_STRATEGY_EXCEPTION_KEYWORDS = [
    "交易制度",
    "上市規則",
    "上櫃規則",
    "市場改革",
    "制度調整",
    "多家公司",
    "多家上市公司",
    "多家上櫃公司",
    "rule change",
    "rule changes",
    "market reform",
    "market structure",
]

PLATFORM_MARKET_RECAP_SOURCES = [
    "富途牛牛",
    "futu niuniu",
    "moomoo",
]

PLATFORM_MARKET_RECAP_KEYWORDS = [
    "what has happened",
    "following each",
    "after each",
    "symposiums on market stabilization",
    "symposium on market stabilization",
    "market stabilization",
    "capital markets following",
    "市場穩定",
    "穩市座談",
    "座談會後",
    "市場怎麼走",
    "市場表現",
    "行情回顧",
]

CRYPTO_PRODUCT_NOISE_KEYWORDS = [
    "DEX",
    "dex",
    "DeFi",
    "defi",
    "TVL",
    "tvl",
    "Solana token",
    "Solana 代幣",
    "代幣交易",
    "token trading",
    "perpetual futures",
    "perpetual",
    "perpetuals",
    "永續合約",
    "主網上線",
    "mainnet",
    "chain TVL",
    "Robinhood Chain",
    "self-custodial trading platform",
    "self-custodial",
    "代幣化股票",
    "launches tokenized stocks",
]

CORE_PRODUCT_STRATEGY_ACTION_KEYWORDS = [
    "regulatory approval",
    "regulatory approved",
    "approved",
    "approval",
    "market-entry regime",
    "omnibus brokerage accounts",
    "brokerage accounts",
    "brokerage account",
    "broker adoption",
    "brokerage platform",
    "exchange",
    "clearing",
    "settlement",
    "on-chain settlement",
    "on-chain clearing",
    "securities settlement",
    "trading venue",
    "market infrastructure",
    "London Stock Exchange",
    "DTCC",
    "金管會核准",
    "主管機關核准",
    "監管核准",
    "券商帳戶",
    "券商採用",
    "證券帳戶",
    "交易所",
    "清算",
    "交割",
    "鏈上結算",
    "鏈上交割",
    "市場基礎設施",
]

LOW_VALUE_REGULATOR_MARKET_KEYWORDS = [
    "投資人先設",
    "風險提醒",
    "被砍倉",
    "上市案證交所通過",
    "上市案",
    "ETF 零股",
    "ETF零股",
    "ETF trading",
    "commission-free ETF",
    "commission-free ETF trading",
    "minimum investment",
    "人氣旺",
    "獨董賦能",
    "銀行獨董",
    "強化調查權",
    "碳排放交易",
    "碳排放交易制度",
    "carbon emissions trading",
    "emissions trading",
    "違約交割",
    "違約買賣",
    "申報違約買賣",
    "違約買賣總額",
    "創今年第",
    "得獎",
    "榜單",
    "named among",
    "top fintech companies",
    "world's top fintech",
    "PR Newswire",
    "where retail investing is headed",
    "thought leadership",
    "全能交易所",
    "預測市場",
    "prediction market",
    "prediction markets",
    "黃金巿場",
    "黃金市場",
    "伊斯蘭債券",
    "人民幣業務",
    "可靠夥伴",
    "進一步合作",
    "further cooperation",
    "gold market",
    "renminbi business",
    "islamic bond",
    "islamic bonds",
]

LOW_VALUE_REGULATOR_EXCEPTION_KEYWORDS = [
    "交易制度",
    "市場制度",
    "系統出包",
    "系統當機",
    "下單",
    "錯帳",
    "限制業務",
    "market structure",
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
        r"違約交割.*(個股|股王|單日|券商通報|翻車)",
        r"零股成交.*(ETF|0050|個股|面板股)",
        r"在與券商互動",
        r"買入.*評級",
        r"公告.*債券.*買賣",
        r"金管會.*裁罰.*(億元|萬元|大單|大罰單|達成率)",
        r"證期局.*裁罰案彙整",
        r"裁罰案彙整.*公開發行公司",
        r"股票禮品卡",
        r"announces full launch.*cfd brokerage platform",
        r"hidden costs of disconnected brokerage systems",
        r"ETF.*散戶.*(損|震盪)",
        r"槓桿\s*ETF.*(散戶|保證金|入場門檻)",
        r"券商.*最低保證金.*ETF",
        r"裁罰.*(銀行業|銀行局).*(大單|大罰單|開鍘|達成率)",
        r"上半年.*裁罰.*(億元|萬元)",
        r"h1.*裁罰.*(億元|萬元)",
        r"金管會.*裁罰.*(風向|重大案件|小案少|大案重)",
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
            "CFTC",
            "NFA",
            "FCA",
            "CIRO",
            "OSC",
            "Ontario Securities Commission",
            "ASIC",
            "MAS",
            "SEBI",
            "CSRC",
            "BaFin",
            "AMF",
            "FINMA",
            "IOSCO",
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
    "CFTC",
    "NFA",
    "FCA",
    "CIRO",
    "OSC",
    "Ontario Securities Commission",
    "ASIC",
    "MAS",
    "SEBI",
    "CSRC",
    "BaFin",
    "AMF",
    "FINMA",
    "CVM",
    "CNBV",
    "DFSA",
    "FSRA",
    "Saudi CMA",
    "FSCA",
    "IOSCO",
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
    "Fidelity",
    "E*TRADE",
    "Webull",
    "SoFi",
    "eToro",
    "DEGIRO",
    "Trading 212",
    "IG Group",
    "XTB",
    "Trade Republic",
    "Scalable Capital",
    "Saxo Bank",
    "Wealthsimple",
    "Questrade",
    "Zerodha",
    "Groww",
    "Upstox",
    "Angel One",
    "CommSec",
    "Stake",
    "Tiger Brokers",
    "Monex",
    "Kiwoom Securities",
]

MAINSTREAM_MEDIA_SOURCES = [
    "工商時報",
    "經濟日報",
    "MoneyDJ",
    "鉅亨",
    "日經",
    "Reuters",
    "FT",
    "Financial Times",
    "WSJ",
    "Yahoo Finance",
    "Bloomberg",
    "Nikkei Asia",
    "SCMP",
    "The Business Times",
    "Caixin",
    "Economic Times",
    "AFR",
    "Financial News London",
    "Handelsblatt",
    "Les Echos",
    "Il Sole 24 Ore",
    "Zawya",
    "The National",
    "Arab News",
    "Business Day",
    "African Markets",
    "Bloomberg Línea",
    "Valor Econômico",
    "AméricaEconomía",
    "El Financiero",
    "CoinDesk",
    "The Block",
    "DL News",
    "Ledger Insights",
    "Blockworks",
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

MARKET_COMMENTARY_SUBJECT_KEYWORDS = [
    "台股",
    "櫃買",
    "櫃買指數",
    "OTC",
    "加權指數",
    "大盤",
    "上市櫃",
    "美股",
    "那斯達克",
    "Nasdaq",
]

MARKET_COMMENTARY_ACTION_KEYWORDS = [
    "季線",
    "長黑",
    "摜破",
    "跌破",
    "重挫",
    "急殺",
    "賣壓",
    "蜂擁賣出",
    "收黑",
    "殺盤",
    "爆殺",
    "震盪",
    "回測",
    "下探",
    "跌勢",
    "大跌",
    "翻黑",
    "失守",
    "plunges",
    "selloff",
    "sell-off",
    "market rout",
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

PRODUCT_PROMOTION_KEYWORDS = [
    "產品介紹",
    "新產品",
    "新品",
    "產品推廣",
    "服務推廣",
    "產品推行",
    "產品導入",
    "解決方案",
    "產品服務",
    "product introduction",
    "new product",
    "product launch",
    "product rollout",
    "product promotion",
    "solution",
    "solutions",
]

FINANCIAL_PRODUCT_TREND_KEYWORDS = [
    "複委託",
    "海外股票",
    "海外交易",
    "美股夜盤",
    "extended-hours trading",
    "24-hour trading",
    "global trading",
    "cross-border trading",
    "RWA",
    "代幣化證券",
    "security token",
    "STO",
    "證券型代幣",
    "tokenized securities",
    "securities tokenized",
    "digital securities",
    "鏈上結算",
    "鏈上交割",
    "on-chain settlement",
    "on-chain clearing",
    "securities settlement",
    "clearing and settlement",
    "virtual asset trading platform",
    "AI投顧",
    "智能投顧",
    "智能下單",
    "AI trading",
    "AI investing",
    "robo-advisor",
    "automated investing",
    "subscription",
    "PFOF",
    "payment for order flow",
]

SINGLE_PRODUCT_SIGNAL_KEYWORDS = [
    "ETF",
    "基金",
    "金融債",
    "債券",
    "ETN",
    "代幣化債券",
    "tokenized bond",
    "stablecoin",
    "穩定幣",
    "交易對",
    "證券代號",
    "ISIN",
]

ROUTINE_PRODUCT_ACTION_KEYWORDS = [
    "開始上市",
    "開始上櫃",
    "上櫃買賣",
    "掛牌",
    "開始櫃檯買賣",
    "開始買賣",
    "證券商營業處所買賣",
    "開放融資融券",
    "得辦理融資融券",
    "得為融資融券",
    "配息公告",
    "淨值公告",
    "成分股調整",
    "發行價格確定",
    "到期",
    "除息",
    "申購截止",
    "新增交易對",
    "lists",
    "listing",
    "listed",
    "trading pair",
    "distribution",
    "net asset value",
    "maturity date",
]

PRODUCT_FIELD_KEYWORDS = [
    "證券代號",
    "ISIN",
    "發行價格",
    "發行總額",
    "到期日",
    "票面利率",
    "交易單位",
    "配息率",
    "經理公司",
    "掛牌日期",
    "流動量提供者",
    "security code",
    "issue price",
    "issue amount",
    "maturity date",
    "coupon rate",
    "trading unit",
    "distribution rate",
    "liquidity provider",
]

EMERGING_PRODUCT_KEYWORDS = [
    "RWA",
    "RWAs",
    "real world asset",
    "real-world asset",
    "代幣化",
    "代幣化證券",
    "代幣化債券",
    "tokenization",
    "tokenized securities",
    "tokenized bond",
    "digital securities",
    "security token",
    "STO",
    "證券型代幣",
    "securities tokenized",
    "鏈上結算",
    "鏈上交割",
    "鏈上清算",
    "鏈上交收",
    "on-chain settlement",
    "on-chain clearing",
    "on-chain securities settlement",
    "on-chain delivery",
    "securities settlement",
    "clearing and settlement",
]

VIRTUAL_ASSET_NOISE_KEYWORDS = [
    "stablecoin",
    "stablecoins",
    "穩定幣",
    "crypto",
    "cryptocurrency",
    "加密貨幣",
    "虛擬資產",
    "virtual asset",
    "digital asset",
    "blockchain finance",
    "on-chain finance",
]

CORE_VIRTUAL_ASSET_STRATEGY_KEYWORDS = [
    "RWA",
    "RWAs",
    "real world asset",
    "real-world asset",
    "代幣化證券",
    "代幣化資產",
    "tokenization",
    "tokenized securities",
    "securities tokenized",
    "digital securities",
    "security token",
    "securities token",
    "STO",
    "證券型代幣",
    "鏈上結算",
    "鏈上交割",
    "鏈上清算",
    "鏈上交收",
    "on-chain settlement",
    "on-chain clearing",
    "on-chain securities settlement",
    "securities settlement",
    "clearing and settlement",
]

PRODUCT_LEGAL_OPENING_KEYWORDS = [
    "通過法案",
    "新規正式上路",
    "主管機關核准",
    "開放券商經營",
    "納入監管",
    "發放新執照",
    "投資人資格",
    "可銷售範圍",
    "adopts",
    "approves",
    "authorizes",
    "license",
    "licence",
    "regulatory framework",
    "market opening",
]

PRODUCT_MECHANICS_CHANGE_KEYWORDS = [
    "區塊鏈發行",
    "數位資產結算",
    "證券結算",
    "現金代幣結算",
    "全天交易",
    "鏈上申購贖回",
    "託管模式",
    "清算與交割",
    "交割方式",
    "跨平台",
    "跨市場流通",
    "on-chain",
    "blockchain issuance",
    "digital asset settlement",
    "token settlement",
    "securities settlement",
    "24-hour trading",
    "custody model",
    "clearing and settlement",
    "settlement method",
    "cross-platform",
    "cross-market",
]

PRODUCT_INSTITUTION_ADOPTION_KEYWORDS = [
    "券商正式上線",
    "銀行正式提供",
    "交易所建立平台",
    "清算機構完成測試",
    "大型資產管理公司推出",
    "多家金融機構",
    "共同參與",
    "組建",
    "成立小組",
    "工作小組",
    "產業小組",
    "聯盟",
    "入列",
    "參與",
    "取得執照後開始營運",
    "task force",
    "working group",
    "consortium",
    "coalition",
    "joins",
    "participates",
    "launches",
    "rolls out",
    "issues",
    "offers",
    "partners",
    "partnership",
    "join forces",
    "joins forces",
    "teams up",
    "backs",
    "合作",
    "投資",
    "上線",
    "adopts",
    "pilot",
    "proof of concept",
]

PRODUCT_BUSINESS_MODEL_KEYWORDS = [
    "新收入來源",
    "手續費模式",
    "入金",
    "借貸",
    "放貸",
    "收益服務",
    "新服務",
    "交易平台",
    "數位資產託管",
    "證券帳戶整合虛擬資產",
    "零售客戶",
    "私募",
    "另類資產",
    "deposit",
    "lending",
    "loan",
    "service",
    "services",
    "trading platform",
    "digital asset custody",
    "securities account",
    "alternative assets",
    "subscription",
    "PFOF",
    "payment for order flow",
]

PRODUCT_BUSINESS_ACTION_KEYWORDS = [
    "推出",
    "將推出",
    "準備推出",
    "計畫推出",
    "上線",
    "將上線",
    "開放",
    "將開放",
    "提供",
    "將提供",
    "申請",
    "測試",
    "試點",
    "布局",
    "佈局",
    "擴大",
    "合作",
    "投資",
    "收購",
    "launch",
    "launches",
    "launching",
    "roll out",
    "rolls out",
    "rollout",
    "is set to",
    "plans to",
    "plan to",
    "offers",
    "offer",
    "opens",
    "open",
    "applies",
    "tests",
    "pilot",
    "partners",
    "expands",
    "invests",
    "acquires",
]

PRODUCT_SPECULATIVE_KEYWORDS = [
    "預測",
    "看好",
    "市值排行",
    "市場規模",
    "price prediction",
    "forecast",
    "reportedly",
]

FUTURE_TONE_KEYWORDS = [
    "將",
    "將要",
    "準備",
    "計畫",
    "預計",
    "可能",
    "擬",
    "may",
    "plans to",
    "plan to",
    "is set to",
    "reportedly",
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
    "交易所",
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
    "CFTC",
    "NFA",
    "FCA",
    "CIRO",
    "OSC",
    "Ontario Securities Commission",
    "ASIC",
    "MAS",
    "SEBI",
    "CSRC",
    "BaFin",
    "AMF",
    "FINMA",
    "CVM",
    "CNBV",
    "DFSA",
    "FSRA",
    "Saudi CMA",
    "FSCA",
    "IOSCO",
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

    for source in sources or RSS_SOURCES:
        if source.name == "DTCC 官方公告":
            entries = _dtcc_press_room_entries(source.url)
            parsed = None
        else:
            parsed = feedparser.parse(source.url)
            entries = list(parsed.entries)
        stats = {
            "raw": len(entries),
            "invalid": 0,
            "duplicate": 0,
            "old": 0,
            "irrelevant": 0,
            "accepted": 0,
        }
        if parsed is not None and getattr(parsed, "bozo", False):
            print(f"Source warning: {source.name} may have a feed issue: {getattr(parsed, 'bozo_exception', 'unknown error')}")

        for entry in entries:
            url = _canonical_url(getattr(entry, "link", "").strip())
            title = _clean_title(getattr(entry, "title", "").strip())
            if not url or not title or url in seen_urls:
                stats["invalid"] += 1
                continue

            title_key = _dedupe_key(title)
            title_tokens = _title_tokens(title)
            if title_key in seen_titles or _is_near_duplicate(title_tokens, seen_title_tokens):
                stats["duplicate"] += 1
                continue

            published_at = _entry_datetime(entry)
            if published_at and published_at < cutoff:
                stats["old"] += 1
                continue

            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            clean_summary = _clean_summary(summary)
            if not _is_relevant(title, clean_summary, source.name, published_at, url):
                stats["irrelevant"] += 1
                continue

            score = _importance_score(title, clean_summary, source.name, published_at)
            article = Article(
                title=title,
                url=url,
                source=source.name,
                published_at=published_at,
                summary=clean_summary,
            )

            seen_urls.add(url)
            seen_titles.add(title_key)
            seen_title_tokens.append(title_tokens)
            scored_articles.append((score, article))
            stats["accepted"] += 1

        print(
            "Source "
            f"{source.name}: raw={stats['raw']}, accepted={stats['accepted']}, "
            f"old={stats['old']}, duplicate={stats['duplicate']}, "
            f"irrelevant={stats['irrelevant']}, invalid={stats['invalid']}"
        )

    scored_articles = _dedupe_similar_events(scored_articles)
    scored_articles.sort(
        key=lambda item: (item[0], item[1].published_at or datetime.min.replace(tzinfo=UTC)),
        reverse=True,
    )
    return [article for _, article in scored_articles]


def _dtcc_press_room_entries(url: str) -> list[SimpleNamespace]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    try:
        html = urlopen(Request(url, headers=headers), timeout=20).read().decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"Source warning: DTCC 官方公告 could not be fetched: {exc}")
        return []

    entries: list[SimpleNamespace] = []
    card_pattern = re.compile(r'<div[^>]+class="post-card"[^>]*>(.*?)</div>\s*</a>', re.IGNORECASE | re.DOTALL)
    link_pattern = re.compile(r'class="post-card__link-wrapper"[^>]+href="([^"]+)"', re.IGNORECASE)
    date_pattern = re.compile(r'class="post-card__date">\s*([^<]+)\s*</span>', re.IGNORECASE)
    title_pattern = re.compile(r'class="post-card__post-link">\s*([^<]+)\s*</span>', re.IGNORECASE)

    for card in card_pattern.findall(html):
        if "Press Releases" not in card:
            continue
        link_match = link_pattern.search(card)
        date_match = date_pattern.search(card)
        title_match = title_pattern.search(card)
        if not link_match or not date_match or not title_match:
            continue

        link = unescape(link_match.group(1).strip())
        if link.startswith("/"):
            link = f"https://www.dtcc.com{link}"

        title = _strip_html(title_match.group(1))
        published = _strip_html(date_match.group(1))
        entries.append(
            SimpleNamespace(
                title=title,
                link=link,
                published=published,
                summary=title,
                description=title,
            )
        )

    return entries


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
            for fmt in ("%B %d, %Y", "%b %d, %Y"):
                try:
                    return datetime.strptime(value.strip(), fmt).replace(tzinfo=UTC)
                except ValueError:
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
    cjk_tokens = _cjk_ngrams(normalized)
    return ascii_tokens | cjk_tokens


def _cjk_ngrams(text: str) -> set[str]:
    tokens: set[str] = set()
    for segment in re.findall(r"[\u4e00-\u9fff]+", text):
        for size in (2, 3, 4):
            if len(segment) < size:
                continue
            tokens.update(segment[index : index + size] for index in range(len(segment) - size + 1))
    return tokens


def _is_near_duplicate(tokens: set[str], seen_token_sets: list[set[str]]) -> bool:
    if len(tokens) < 3:
        return False

    for seen_tokens in seen_token_sets:
        overlap = len(tokens & seen_tokens)
        union = len(tokens | seen_tokens)
        if union and overlap / union >= 0.42:
            return True
    return False


def _dedupe_similar_events(scored_articles: list[tuple[int, Article]]) -> list[tuple[int, Article]]:
    selected: list[tuple[int, Article]] = []
    candidates = sorted(scored_articles, key=_article_priority, reverse=True)
    removed_count = 0

    for score, article in candidates:
        duplicate_index = None
        for index, (_, selected_article) in enumerate(selected):
            if _is_same_event(article, selected_article):
                duplicate_index = index
                break

        if duplicate_index is None:
            selected.append((score, article))
            continue

        existing = selected[duplicate_index]
        removed_count += 1
        if _article_priority((score, article)) > _article_priority(existing):
            selected[duplicate_index] = (score, article)

    if removed_count:
        print(f"Deduped {removed_count} similar event articles.")

    return selected


def _article_priority(item: tuple[int, Article]) -> tuple[float, int, datetime]:
    score, article = item
    published_at = article.published_at or datetime.min.replace(tzinfo=UTC)
    return (score, _source_authority_score(article.source), published_at)


def _is_same_event(article: Article, other: Article) -> bool:
    article_key = _event_key(article.title)
    other_key = _event_key(other.title)
    if article_key and article_key == other_key:
        return True

    fp = _event_fingerprint(article)
    other_fp = _event_fingerprint(other)
    title_similarity = _token_similarity(_title_tokens(article.title), _title_tokens(other.title))
    text_similarity = _token_similarity(_content_tokens(article), _content_tokens(other))
    signature_similarity = _token_similarity(_event_signature_tokens(article), _event_signature_tokens(other))

    if title_similarity >= 0.58 or text_similarity >= 0.50:
        return True

    if signature_similarity >= 0.45:
        return True

    shared_topics = fp["topics"] & other_fp["topics"]
    shared_actions = fp["actions"] & other_fp["actions"]
    shared_regions = fp["regions"] & other_fp["regions"]
    shared_actors = fp["actors"] & other_fp["actors"]
    same_day = _same_publication_day(article, other)
    same_day_topic_dedupe_topics = {"stock_gift_card", "financial_cyber_ai"}
    strong_event_topics = {
        "stock_gift_card",
        "financial_cyber_ai",
        "tokenization_rwa",
        "settlement",
        "market_structure",
        "cross_border",
        "broker_app",
        "business_model",
    }

    if _event_family(article) and _event_family(article) == _event_family(other) and same_day:
        return True

    if len(_specific_actor_tokens(article) & _specific_actor_tokens(other)) >= 2 and same_day:
        return True

    if same_day and shared_topics & same_day_topic_dedupe_topics:
        return True

    if same_day and shared_topics & strong_event_topics and (shared_regions or shared_actors or shared_actions):
        return True

    if same_day and shared_topics and shared_actors:
        return True

    if _same_specific_actor(article, other) and shared_topics and shared_actions:
        return True

    if _same_specific_actor(article, other) and shared_topics and (text_similarity >= 0.20 or signature_similarity >= 0.30):
        return True

    return False


def _same_publication_day(article: Article, other: Article) -> bool:
    if not article.published_at or not other.published_at:
        return True
    return article.published_at.date() == other.published_at.date()


def _event_family(article: Article) -> str | None:
    fp = _event_fingerprint(article)
    if not fp["topics"]:
        return None

    region = sorted(fp["regions"])[0] if fp["regions"] else "global"
    topic = sorted(fp["topics"])[0]

    if "institution_group" in fp["actions"]:
        return f"{topic}:institution_group:{region}"
    if "regulation" in fp["actions"]:
        return f"{topic}:regulation:{region}"
    if "infrastructure" in fp["actions"]:
        return f"{topic}:infrastructure:{region}"
    if "launch_adoption" in fp["actions"] and fp["actors"]:
        actor = sorted(fp["actors"])[0]
        return f"{topic}:launch_adoption:{region}:{actor}"
    if "partnership" in fp["actions"] and fp["actors"]:
        actor = sorted(fp["actors"])[0]
        return f"{topic}:partnership:{region}:{actor}"

    return None


def _same_specific_actor(article: Article, other: Article) -> bool:
    return bool(_specific_actor_tokens(article) & _specific_actor_tokens(other))


def _specific_actor_tokens(article: Article) -> set[str]:
    text = f"{article.title}\n{article.summary}".lower()
    actors: set[str] = set()
    specific_keywords = BROKERAGE_NAMES + OFFICIAL_SOURCES + [
        "Solana",
        "貝萊德",
        "摩根大通",
        "BlackRock",
        "JPMorgan",
        "JP Morgan",
        "DTCC",
    ]
    for keyword in specific_keywords:
        if _contains_keyword(text, keyword):
            actors.add(_dedupe_key(keyword))
    return actors


def _event_fingerprint(article: Article) -> dict[str, set[str]]:
    text = f"{article.title}\n{article.summary}".lower()
    return {
        "topics": _fingerprint_topics(text),
        "actions": _fingerprint_actions(text),
        "regions": _fingerprint_regions(text, article.source),
        "actors": _fingerprint_actors(text),
    }


def _fingerprint_topics(lower_text: str) -> set[str]:
    topics: set[str] = set()
    topic_groups = {
        "tokenization_rwa": [
            "RWA",
            "RWAs",
            "real world asset",
            "real-world asset",
            "代幣化",
            "tokenization",
            "tokenized securities",
            "blockchain finance",
            "on-chain finance",
        ],
        "stablecoin": ["stablecoin", "stablecoins", "穩定幣"],
        "virtual_asset": ["virtual asset", "虛擬資產", "digital asset", "on-chain finance", "blockchain finance"],
        "market_structure": ["交易制度", "market structure", "market design", "撮合", "逐筆交易"],
        "settlement": ["交割", "清算", "settlement", "clearing", "central counterparty"],
        "stock_gift_card": ["股票禮品卡", "禮品卡", "stock gift card", "gift card"],
        "financial_cyber_ai": ["AI攻擊", "ai攻擊", "金融資安", "資安", "cybersecurity", "cyber attack", "AI attack"],
        "cross_border": ["複委託", "海外交易", "海外股票", "cross-border", "global trading"],
        "broker_app": ["trading app", "broker app", "online brokerage", "digital brokerage"],
        "ai_investing": ["AI投顧", "智能投顧", "AI investing", "robo-advisor", "automated investing"],
        "business_model": ["subscription", "PFOF", "payment for order flow", "入金", "託管", "custody"],
    }
    for topic, keywords in topic_groups.items():
        if any(_contains_keyword(lower_text, keyword) for keyword in keywords):
            topics.add(topic)
    return topics


def _fingerprint_actions(lower_text: str) -> set[str]:
    actions: set[str] = set()
    action_groups = {
        "regulation": PRODUCT_LEGAL_OPENING_KEYWORDS + ["修法", "法規", "監管", "regulatory"],
        "institution_group": [
            "組建",
            "成立小組",
            "工作小組",
            "產業小組",
            "聯盟",
            "共同參與",
            "入列",
            "task force",
            "working group",
            "consortium",
            "coalition",
            "joins",
            "participates",
        ],
        "launch_adoption": PRODUCT_INSTITUTION_ADOPTION_KEYWORDS + [
            "推出",
            "上線",
            "launch",
            "launches",
            "backs",
            "backing",
            "落地",
            "開放",
        ],
        "infrastructure": ["交易所建立平台", "清算機構", "clearing", "settlement", "平台", "market infrastructure"],
        "partnership": ["合作", "partners", "partnership", "joint venture"],
        "test_pilot": ["試點", "概念驗證", "pilot", "proof of concept", "測試"],
        "acquisition": ["收購", "合併", "acquisition", "merger"],
    }
    for action, keywords in action_groups.items():
        if any(_contains_keyword(lower_text, keyword) for keyword in keywords):
            actions.add(action)
    return actions


def _fingerprint_regions(lower_text: str, source: str) -> set[str]:
    regions: set[str] = set()
    region_terms = {
        "uk": ["英國", "uk", "u.k.", "britain"],
        "us": ["美國", "us", "u.s.", "united states", "SEC", "FINRA", "CFTC", "NFA"],
        "japan": ["日本", "japan"],
        "hong_kong": ["香港", "hong kong"],
        "taiwan": ["台灣", "臺灣", "taiwan", "金管會", "證交所", "櫃買"],
        "korea": ["韓國", "korea"],
        "china": ["中國", "china"],
        "singapore": ["新加坡", "singapore", "MAS"],
        "india": ["印度", "india", "SEBI"],
        "canada": ["加拿大", "canada", "CIRO", "OSC", "Ontario Securities Commission"],
        "australia": ["澳洲", "australia", "ASIC"],
        "eu": ["歐盟", "eu", "ESMA", "BaFin", "AMF"],
        "switzerland": ["瑞士", "switzerland", "FINMA"],
        "latin_america": ["巴西", "墨西哥", "brazil", "mexico", "CVM", "CNBV"],
        "middle_east": ["dubai", "abu dhabi", "saudi", "DFSA", "FSRA", "Saudi CMA"],
        "africa": ["南非", "south africa", "FSCA"],
    }
    lower_source = source.lower()
    for region, keywords in region_terms.items():
        if any(_contains_keyword(lower_text, keyword) or _contains_keyword(lower_source, keyword) for keyword in keywords):
            regions.add(region)
    return regions


def _fingerprint_actors(lower_text: str) -> set[str]:
    actors: set[str] = set()
    actor_keywords = (
        BROKERAGE_NAMES
        + OFFICIAL_SOURCES
        + [
            "貝萊德",
            "摩根大通",
            "BlackRock",
            "JPMorgan",
            "JP Morgan",
            "Solana",
            "DigiFT",
            "JX",
            "JPYSC",
            "交易所",
            "清算機構",
            "銀行",
            "券商",
            "證券商",
            "asset manager",
            "bank",
            "exchange",
            "clearing house",
        ]
    )
    for keyword in actor_keywords:
        if _contains_keyword(lower_text, keyword):
            actors.add(_dedupe_key(keyword))
    return actors


def _content_tokens(article: Article) -> set[str]:
    return _title_tokens(f"{article.title} {article.summary}")


def _event_signature_tokens(article: Article) -> set[str]:
    text = f"{article.title} {article.summary}".lower()
    tokens = set(re.findall(r"[a-z0-9]{3,}", text))
    tokens |= _cjk_ngrams(text)
    noise = {
        "新聞",
        "市場",
        "表示",
        "指出",
        "今日",
        "今年",
        "最新",
        "moneydj",
        "reuters",
        "finance",
    }
    return {token for token in tokens if token not in noise and len(token) >= 2}


def _token_similarity(tokens: set[str], other_tokens: set[str]) -> float:
    if not tokens or not other_tokens:
        return 0.0
    return len(tokens & other_tokens) / len(tokens | other_tokens)


def _event_key(title: str) -> str | None:
    lower_title = title.lower()
    compact_title = re.sub(r"\s+", "", lower_title)
    if "股票禮品卡" in title and ("金管會" in title or "券商" in title or "永豐金證券" in title):
        return "tw_stock_gift_card_sandbox"

    if ("digift" in lower_title or "sbi" in lower_title) and (
        "jx" in lower_title
        or "jx 代幣" in title
        or "jpysc" in lower_title
        or "tokenized securities" in lower_title
        or "區塊鏈" in title
        or "鏈上金融" in title
        or "defi" in lower_title
    ):
        return "sbi_digift_jx_tokenized_securities"

    if "金管會" in title and "裁罰" in title and any(
        keyword in title for keyword in ["上半年", "H1", "近億元", "9787", "9,787", "銀行業", "大罰單", "達成率"]
    ):
        return "tw_fsc_h1_penalty_statistics"

    taishin_system_terms = ["台新證", "台新證券", "系統", "app", "下單", "錯帳", "當機", "出包", "災情"]
    taishin_penalty_terms = ["金管會", "裁罰", "重罰", "360萬", "360 萬", "限制", "史上最高", "最重罰"]
    if any(keyword.lower() in lower_title for keyword in taishin_system_terms) and any(
        keyword.lower() in lower_title for keyword in taishin_penalty_terms
    ):
        return "tw_taishin_securities_system_penalty"

    if "券商" in title and "系統" in title and any(
        keyword in title for keyword in ["金管會", "裁罰", "重罰", "360萬", "360 萬", "史上最高", "最重罰"]
    ):
        return "tw_taishin_securities_system_penalty"

    if ("金管會" in title or "金融" in title) and (
        "ai攻擊" in compact_title or "金融資安" in title or ("打敗" in title and "AI" in title)
    ):
        return "tw_fsc_financial_ai_cybersecurity"

    if "零股" in title and any(keyword in title for keyword in ["撮合", "9點", "提前", "提早", "開盤"]):
        return "tw_fractional_lot_reform"

    if "gemini" in lower_title and "stock trading" in lower_title and (
        "commission" in lower_title or "commission-free" in lower_title
    ):
        return "gemini_zero_commission_stock_trading"

    if "中國信託證券" in title and "複委託" in title:
        return "ctbc_securities_sub_brokerage_campaign"

    return None


def _is_relevant(
    title: str,
    summary: str,
    source: str,
    published_at: datetime | None,
    url: str = "",
) -> bool:
    lower_title = title.lower()
    lower_text = f"{title}\n{summary}".lower()
    lower_url = url.lower()

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

    if any(keyword.lower() in lower_text for keyword in ABSOLUTE_EXCLUDE_KEYWORDS) or any(
        pattern.search(f"{title}\n{summary}") for pattern in ABSOLUTE_EXCLUDE_PATTERNS
    ):
        return False

    if _is_broker_earnings_or_stock_news(lower_text):
        return False

    if _is_broker_commentary_on_non_broker_industry(lower_title, lower_text):
        return False

    if _is_individual_trading_status_announcement(lower_text):
        return False

    if _is_platform_market_recap(lower_title, lower_text, source):
        return False

    if _is_non_core_crypto_product_news(lower_text):
        return False

    if _is_low_value_regulator_or_market_item(lower_text):
        return False

    if _is_individual_investor_alert(lower_title, lower_text, lower_url, source):
        return False

    if _has_individual_alert_signal(lower_text, lower_url) and _has_alert_strategy_exception(lower_text):
        return True

    if _is_individual_corporate_filing(lower_text):
        return False

    if _has_corporate_filing_strategy_exception(lower_text):
        return True

    if hard_noise_hit:
        return False

    if _is_non_core_virtual_asset_news(lower_text):
        return False

    product_level = _product_event_level(title, summary, source)
    if product_level == 0:
        return False
    product_strategy_candidate = product_level in {1, 2, 3}

    if _has_emerging_product_signal(lower_text) and not _has_product_strategy_exception(lower_text, source):
        return False

    if _is_investor_or_product_content(lower_text):
        return False

    if _is_market_price_commentary(lower_text):
        return False

    if _is_non_focus_product_promotion(lower_title, lower_text, source):
        return False

    if _is_education_or_profile_content(lower_text):
        return False

    if product_level not in {2, 3} and _is_non_focus_tech_vendor_article(lower_title, lower_text, source):
        return False

    if not product_strategy_candidate and not _has_required_focus(lower_title, lower_text, source):
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


def _is_alert_list_url(lower_url: str) -> bool:
    return any(keyword in lower_url for keyword in ALERT_LIST_URL_KEYWORDS)


def _has_individual_alert_signal(lower_text: str, lower_url: str = "") -> bool:
    return _is_alert_list_url(lower_url) or any(
        _contains_keyword(lower_text, keyword) for keyword in INDIVIDUAL_ALERT_KEYWORDS
    )


def _has_alert_strategy_exception(lower_text: str) -> bool:
    if any(_contains_keyword(lower_text, keyword) for keyword in ALERT_STRATEGY_EXCEPTION_KEYWORDS):
        return True
    return any(_contains_keyword(lower_text, keyword) for keyword in BROKERAGE_NAMES)


def _is_individual_investor_alert(lower_title: str, lower_text: str, lower_url: str = "", source: str = "") -> bool:
    if not _has_individual_alert_signal(lower_text, lower_url) and not _is_sfc_single_entity_alert_title(
        lower_title, source
    ):
        return False
    return not _has_alert_strategy_exception(lower_text)


def _is_sfc_single_entity_alert_title(lower_title: str, source: str) -> bool:
    lower_source = source.lower()
    if "香港證監會" not in lower_source and "sfc" not in lower_source:
        return False
    if " - securities & futures commission of hong kong" not in lower_title:
        return False

    entity_part = lower_title.split(" - securities & futures commission of hong kong", maxsplit=1)[0].strip()
    if not entity_part:
        return False

    policy_terms = [
        "statement",
        "circular",
        "consultation",
        "guideline",
        "policy",
        "rules",
        "regulation",
        "enforcement",
        "market",
        "industry",
        "fatf",
    ]
    if any(term in entity_part for term in policy_terms):
        return False

    entity_terms = [
        "limited",
        "ltd",
        "company",
        "capital",
        "management",
        "services",
        "asset",
        "group",
        "platform",
        "investment",
        "finance",
        "wealth",
        "www.",
        ".com",
    ]
    return any(term in entity_part for term in entity_terms)


def _is_individual_corporate_filing(lower_text: str) -> bool:
    if not any(_contains_keyword(lower_text, keyword) for keyword in INDIVIDUAL_CORPORATE_FILING_KEYWORDS):
        return False

    if _has_corporate_filing_strategy_exception(lower_text):
        return False

    if any(_contains_keyword(lower_text, keyword) for keyword in BROKERAGE_NAMES):
        return False

    return True


def _has_corporate_filing_strategy_exception(lower_text: str) -> bool:
    return any(_contains_keyword(lower_text, keyword) for keyword in CORPORATE_FILING_STRATEGY_EXCEPTION_KEYWORDS)


def _is_broker_earnings_or_stock_news(lower_text: str) -> bool:
    if not any(_contains_keyword(lower_text, keyword) for keyword in BROKERAGE_NAMES):
        return False

    if not any(_contains_keyword(lower_text, keyword) for keyword in BROKER_EARNINGS_NOISE_KEYWORDS):
        return False

    return not any(
        _contains_keyword(lower_text, keyword) for keyword in BROKER_EARNINGS_STRATEGY_EXCEPTION_KEYWORDS
    )


def _is_broker_commentary_on_non_broker_industry(lower_title: str, lower_text: str) -> bool:
    marker_hit = any(marker.lower() in lower_title for marker in BROKER_COMMENTARY_MARKERS) or any(
        [
            re.search(r"券商[^：:]{0,40}[：:]", lower_title, re.IGNORECASE) is not None,
            re.search(r"(證券|securities)[^：:]{0,40}[：:]", lower_title, re.IGNORECASE) is not None
            and any(_contains_keyword(lower_title, keyword) for keyword in BROKERAGE_NAMES),
        ]
    )
    if not marker_hit:
        return False

    if not any(_contains_keyword(lower_text, keyword) for keyword in NON_BROKER_INDUSTRY_COMMENTARY_KEYWORDS):
        return False

    return not any(
        _contains_keyword(lower_text, keyword)
        for keyword in MARKET_RULE_CORE_TERMS
        + [
            "裁罰",
            "系統出包",
            "系統當機",
            "錯帳",
            "下單",
            "限制業務",
            "market-entry regime",
            "regulatory approval",
            "tokenized securities",
            "on-chain settlement",
            "鏈上交割",
            "鏈上結算",
        ]
    )


def _is_individual_trading_status_announcement(lower_text: str) -> bool:
    terminal_status_hit = any(
        _contains_keyword(lower_text, keyword)
        for keyword in [
            "終止興櫃買賣",
            "終止興櫃",
            "終止買賣",
        ]
    )
    if terminal_status_hit and not any(
        _contains_keyword(lower_text, keyword) for keyword in TRADING_STATUS_STRATEGY_EXCEPTION_KEYWORDS
    ):
        return True

    status_hits = sum(1 for keyword in INDIVIDUAL_TRADING_STATUS_KEYWORDS if _contains_keyword(lower_text, keyword))
    if status_hits < 2:
        return False

    return not any(_contains_keyword(lower_text, keyword) for keyword in TRADING_STATUS_STRATEGY_EXCEPTION_KEYWORDS)


def _is_platform_market_recap(lower_title: str, lower_text: str, source: str) -> bool:
    lower_source = source.lower()
    combined = f"{lower_title}\n{lower_text}\n{lower_source}"
    platform_hit = any(keyword in combined for keyword in PLATFORM_MARKET_RECAP_SOURCES)
    if not platform_hit:
        return False

    recap_hit = any(_contains_keyword(combined, keyword) for keyword in PLATFORM_MARKET_RECAP_KEYWORDS)
    if not recap_hit:
        return False

    return not any(
        _contains_keyword(combined, keyword)
        for keyword in [
            "new rule",
            "new rules",
            "rule change",
            "new policy",
            "policy change",
            "market-entry regime",
            "market entry",
            "license",
            "licensing",
            "政策",
            "新規",
            "牌照",
        ]
    )


def _is_non_core_crypto_product_news(lower_text: str) -> bool:
    if not any(_contains_keyword(lower_text, keyword) for keyword in CRYPTO_PRODUCT_NOISE_KEYWORDS):
        return False

    return not _has_core_product_strategy_action(lower_text)


def _has_core_product_strategy_action(lower_text: str) -> bool:
    regulatory_account_access = any(
        _contains_keyword(lower_text, keyword)
        for keyword in ["regulatory approval", "approved", "approval", "監管核准", "主管機關核准"]
    ) and any(
        _contains_keyword(lower_text, keyword)
        for keyword in [
            "omnibus brokerage accounts",
            "brokerage accounts",
            "brokerage account",
            "individual investors",
            "券商帳戶",
            "證券帳戶",
            "投資人資格",
        ]
    )
    if regulatory_account_access:
        return True

    named_market_infrastructure = any(
        _contains_keyword(lower_text, keyword)
        for keyword in ["London Stock Exchange", "LSE", "DTCC", "clearing house", "清算機構", "交易所"]
    ) and any(
        _contains_keyword(lower_text, keyword)
        for keyword in [
            "trading venue",
            "market infrastructure",
            "on-chain settlement",
            "on-chain clearing",
            "securities settlement",
            "clearing and settlement",
            "鏈上結算",
            "鏈上交割",
            "清算交割",
        ]
    )
    if named_market_infrastructure:
        return True

    broker_market_entry = any(
        _contains_keyword(lower_text, keyword) for keyword in ["market-entry regime", "market entry", "市場進入"]
    ) and any(_contains_keyword(lower_text, keyword) for keyword in BROKERAGE_NAMES + BROKERAGE_CORE_TERMS)
    if broker_market_entry:
        return True

    return False


def _is_low_value_regulator_or_market_item(lower_text: str) -> bool:
    if not any(_contains_keyword(lower_text, keyword) for keyword in LOW_VALUE_REGULATOR_MARKET_KEYWORDS):
        return False

    if any(
        _contains_keyword(lower_text, keyword)
        for keyword in ["碳排放交易", "碳排放交易制度", "carbon emissions trading", "emissions trading"]
    ):
        return True

    if any(_contains_keyword(lower_text, keyword) for keyword in LOW_VALUE_REGULATOR_EXCEPTION_KEYWORDS):
        return False

    return True


def _product_event_level(title: str, summary: str, source: str) -> int | None:
    text = f"{title}\n{summary}".lower()
    product_identifier_hits = _product_identifier_hits(text)
    single_product_hits = _count_contains(text, SINGLE_PRODUCT_SIGNAL_KEYWORDS) + product_identifier_hits
    routine_action_hits = _count_contains(text, ROUTINE_PRODUCT_ACTION_KEYWORDS)
    product_field_hits = _count_contains(text, PRODUCT_FIELD_KEYWORDS) + _product_field_pattern_hits(text)

    if (
        routine_action_hits >= 1
        and (
            (single_product_hits >= 1 and product_field_hits >= 2)
            or product_identifier_hits >= 1
        )
        and not _has_product_strategy_exception(text, source)
    ):
        return 0

    legal_or_infra = _count_contains(text, PRODUCT_LEGAL_OPENING_KEYWORDS) or any(
        _contains_keyword(text, keyword)
        for keyword in ["交易所建立平台", "清算機構", "market infrastructure", "clearing", "settlement"]
    )
    if legal_or_infra and _has_emerging_product_signal(text):
        return 3

    multi_institution_or_model = _has_financial_product_business_action(text) or _count_contains(text, PRODUCT_BUSINESS_MODEL_KEYWORDS) or (
        _institution_adoption_hits(text) and _has_financial_institution_context(text)
    )
    if multi_institution_or_model and _has_emerging_product_signal(text):
        return 2

    single_company_product = _has_emerging_product_signal(text) and (
        _institution_adoption_hits(text)
        or _count_contains(text, PRODUCT_PROMOTION_KEYWORDS)
    )
    if single_company_product:
        return 1

    return None


def _product_event_score(title: str, summary: str, source: str) -> int:
    text = f"{title}\n{summary}".lower()
    score = 0
    level = _product_event_level(title, summary, source)

    if level == 0:
        score -= 8
    elif level == 1:
        score += 2
    elif level == 2:
        score += 7
    elif level == 3:
        score += 11

    if _count_contains(text, PRODUCT_LEGAL_OPENING_KEYWORDS):
        score += 8
    if any(_contains_keyword(text, keyword) for keyword in ["交易所建立平台", "清算機構", "clearing", "settlement"]):
        score += 7
    if _institution_adoption_hits(text) and _has_financial_institution_context(text):
        score += 5
    if _count_contains(text, PRODUCT_MECHANICS_CHANGE_KEYWORDS):
        score += 5
    if any(_contains_keyword(text, keyword) for keyword in ["license", "licence", "執照"]):
        score += 5
    if any(_contains_keyword(text, keyword) for keyword in ["pilot", "proof of concept", "試點", "概念驗證"]):
        score += 3
    if _has_emerging_product_signal(text):
        score += 1

    if _count_contains(text, ROUTINE_PRODUCT_ACTION_KEYWORDS):
        score -= 6
    if _count_contains(text, PRODUCT_FIELD_KEYWORDS) + _product_field_pattern_hits(text) >= 2:
        score -= 4
    if any(_contains_keyword(text, keyword) for keyword in ["配息", "淨值", "到期", "利率", "distribution", "net asset value"]):
        score -= 6
    if any(_contains_keyword(text, keyword) for keyword in ["新增交易對", "trading pair"]):
        score -= 5
    if any(_contains_keyword(text, keyword) for keyword in ["價格", "市值", "績效", "price", "market cap", "performance"]):
        score -= 6
    if _count_contains(text, PRODUCT_PROMOTION_KEYWORDS):
        score -= 4
    if _count_contains(text, PRODUCT_SPECULATIVE_KEYWORDS):
        score -= 3
    if _has_future_tone_without_concrete_strategy(text):
        score -= 2

    return score


def _has_product_strategy_exception(lower_text: str, source: str) -> bool:
    return any(
        [
            _count_contains(lower_text, PRODUCT_LEGAL_OPENING_KEYWORDS) > 0,
            _count_contains(lower_text, PRODUCT_MECHANICS_CHANGE_KEYWORDS) > 0,
            _count_contains(lower_text, PRODUCT_BUSINESS_MODEL_KEYWORDS) > 0,
            _has_financial_product_business_action(lower_text),
            _institution_adoption_hits(lower_text) > 0
            and _has_financial_institution_context(lower_text),
        ]
    )


def _has_emerging_product_signal(lower_text: str) -> bool:
    return _count_contains(lower_text, EMERGING_PRODUCT_KEYWORDS) > 0


def _has_core_virtual_asset_strategy_signal(lower_text: str) -> bool:
    return _count_contains(lower_text, CORE_VIRTUAL_ASSET_STRATEGY_KEYWORDS) > 0


def _is_non_core_virtual_asset_news(lower_text: str) -> bool:
    if not _count_contains(lower_text, VIRTUAL_ASSET_NOISE_KEYWORDS):
        return False
    return not _has_core_virtual_asset_strategy_signal(lower_text)


def _has_financial_product_business_action(lower_text: str) -> bool:
    return (
        _has_emerging_product_signal(lower_text)
        and _has_financial_institution_context(lower_text)
        and any(_contains_keyword(lower_text, keyword) for keyword in PRODUCT_BUSINESS_ACTION_KEYWORDS + PRODUCT_BUSINESS_MODEL_KEYWORDS)
    )


def _has_future_tone_without_concrete_strategy(lower_text: str) -> bool:
    if not any(_contains_keyword(lower_text, keyword) for keyword in FUTURE_TONE_KEYWORDS):
        return False
    return not _has_financial_product_business_action(lower_text)


def _has_financial_institution_context(lower_text: str) -> bool:
    return any(
        _contains_keyword(lower_text, keyword)
        for keyword in BROKERAGE_NAMES
        + BROKERAGE_CORE_TERMS
        + [
            "銀行",
            "交易所",
            "清算機構",
            "資產管理公司",
            "大行",
            "貝萊德",
            "摩根大通",
            "BlackRock",
            "JPMorgan",
            "JP Morgan",
            "financial institution",
            "bank",
            "exchange",
            "clearing house",
            "asset manager",
        ]
    )


def _institution_adoption_hits(lower_text: str) -> int:
    hits = _count_contains(lower_text, PRODUCT_INSTITUTION_ADOPTION_KEYWORDS)
    patterns = [
        r"(券商|證券商|銀行|交易所|清算機構|資產管理公司).{0,20}(推出|發行|建立|上線|提供|合作|測試|採用)",
        r"(broker|brokerage|bank|exchange|clearing house|asset manager).{0,40}(launches|issues|offers|builds|partners|adopts|tests)",
    ]
    return hits + sum(1 for pattern in patterns if re.search(pattern, lower_text, re.IGNORECASE))


def _count_contains(lower_text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if _contains_keyword(lower_text, keyword))


def _product_identifier_hits(lower_text: str) -> int:
    patterns = [
        r"\bisin[:：]?\s*[a-z]{2}[a-z0-9]{10}\b",
        r"\b[A-Z]{2}[A-Z0-9]{10}\b",
        r"\b[A-Z]\d{2}[A-Z]{3,6}\d{2,4}\b",
        r"[「\"]?[A-Z0-9]{6,12}[」\"]?",
        r"證券代號[:：]?\s*\w+",
        r"\b\d{4,6}[A-Z]?\b",
    ]
    return sum(1 for pattern in patterns if re.search(pattern, lower_text, re.IGNORECASE))


def _product_field_pattern_hits(lower_text: str) -> int:
    patterns = [
        r"發行(價格|總額)[:：]?",
        r"到期(日)?[:：]?",
        r"票面利率[:：]?",
        r"交易單位[:：]?",
        r"配息率[:：]?",
        r"掛牌日期[:：]?",
    ]
    return sum(1 for pattern in patterns if re.search(pattern, lower_text, re.IGNORECASE))


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


def _is_market_price_commentary(lower_text: str) -> bool:
    subject_hit = any(_contains_keyword(lower_text, keyword) for keyword in MARKET_COMMENTARY_SUBJECT_KEYWORDS)
    action_hit = any(_contains_keyword(lower_text, keyword) for keyword in MARKET_COMMENTARY_ACTION_KEYWORDS)
    if not subject_hit or not action_hit:
        return False

    return not any(
        _contains_keyword(lower_text, keyword)
        for keyword in [
            "交易制度",
            "市場制度",
            "market structure",
            "market design",
            "法規",
            "監理",
            "修法",
            "通過",
            "核准",
            "正式上路",
            "清算",
            "交割",
            "settlement",
            "clearing",
        ]
    )


def _is_non_focus_product_promotion(lower_title: str, lower_text: str, source: str) -> bool:
    product_hit = any(_contains_keyword(lower_text, keyword) for keyword in PRODUCT_PROMOTION_KEYWORDS)
    if not product_hit:
        return False

    if not _has_required_focus(lower_title, lower_text, source):
        return True

    return not any(_contains_keyword(lower_text, keyword) for keyword in FINANCIAL_PRODUCT_TREND_KEYWORDS)


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
    score += _product_event_score(title, summary, source)
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
        score -= _investor_alert_penalty(title, summary)

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


def _investor_alert_penalty(title: str, summary: str) -> int:
    text = f"{title}\n{summary}".lower()
    if not _has_individual_alert_signal(text):
        return 0
    if _has_alert_strategy_exception(text):
        return 0
    return 8


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
